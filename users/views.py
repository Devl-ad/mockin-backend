from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import pyotp
from account.models import Kyc
from django.db.models import Sum
from baseapp import utils
from users.models import Notification, Transactions, Packages, Investments
from .forms import DepositForm, KycForm, UpdateUserForm, ChangePasswordForm
from django.contrib.auth import update_session_auth_hash
from account.models import PaymenyDetails
import datetime
from django.http import JsonResponse
from .serializer import TnxSerializer


@login_required()
def index(request):
    user = request.user
    current_date = datetime.datetime.now()
    month = current_date.month
    year = current_date.year

    try:
        paydetail = PaymenyDetails.objects.get(user=user)
    except PaymenyDetails.DoesNotExist:
        paydetail = None

    recent_trasaction = Transactions.objects.filter(user=user).order_by("-date")[:1]

    total_deposit = Transactions.objects.filter(
        user=user, trans_type=utils.D, status="approved"
    ).aggregate(total_deposi=Sum("amount"))
    total_deposit_result = total_deposit["total_deposi"] or 0

    # Calculate the total amount received by the user for the current month
    total_deposit_month = Transactions.objects.filter(
        user=user,
        trans_type=utils.D,
        status="approved",
        date__year=year,
        date__month=month,
    ).aggregate(total_amount_received=Sum("amount"))

    total_with_month = Transactions.objects.filter(
        user=user,
        status="approved",
        trans_type=utils.W,
        date__year=year,
        date__month=month,
    ).aggregate(total_amount_received=Sum("amount"))

    context = {
        "investment_count": Investments.objects.filter(user=user).count(),
        "total_deposit": total_deposit_result,
        "total_deposit_month": total_deposit_month["total_amount_received"] or 0,
        "total_with_month": total_with_month["total_amount_received"] or 0,
        "recent_trasaction": recent_trasaction,
        "paydetail": paydetail,
    }
    return render(request, "useri/index.html", context)


@login_required()
def deposit_page(request):
    if request.POST:
        amount = int(request.POST.get("amount"))
        method = request.POST.get("mode")
        return redirect("deposit_confrim", amount=amount, mode=method)
    return render(request, "useri/deposit.html")


@login_required()
def deposit_confrim(request, amount, mode):
    user = request.user
    if mode in utils.wallets and amount >= 50:
        if request.POST:
            form = DepositForm(request.POST, request.FILES)
            if form.is_valid():
                instance = form.save(commit=False)
                instance.user = user

                form.save()

                messages.error(
                    request,
                    f"a deposit of ${amount} has been created it now under review",
                )

                return redirect("deposit_page")
        else:
            context = {
                "amount": amount,
                "mode": mode,
                "address": utils.ADMIN_ADDRESS[mode],
                "txid": f"TX{utils.rand_code()}",
            }
            return render(request, "useri/deposit-confirm.html", context)

    else:
        messages.error(request, "Invalid Link")
        return redirect("deposit_page")


@login_required()
def withdrawal(request):
    user = request.user
    # if user.is_verified != True:
    #     messages.error(request, "Verify Your Account")
    #     return redirect("kyc")

    if request.POST:
        amount = int(request.POST.get("amount"))
        mode = request.POST.get("mode")
        # addr = utils.check_user_address(user)
        try:
            paydetail = PaymenyDetails.objects.get(user=user)
        except PaymenyDetails.DoesNotExist:
            paydetail = None
        if paydetail:
            if user.balance >= amount:
                transaction = Transactions(
                    user=user,
                    amount=amount,
                    method=mode,
                    trans_type=utils.W,
                    unique_u=f"TX{utils.rand_code()}",
                )
                user.balance -= amount
                user.save()
                transaction.save()

                messages.error(
                    request,
                    "Withdraw request created successfully it's now under review",
                )
                return redirect("withdrawal")
            else:
                messages.error(request, "Insuficient Funds")
                return redirect("withdrawal")
        else:
            messages.error(request, "Please Update your withdrawal addresses")
            return redirect("withdrawal")
    return render(request, "useri/withdrawal.html")


@login_required()
def transactions_page(request):
    transactions = Transactions.objects.filter(user=request.user).order_by("-date")
    return render(request, "useri/transactions.html", {"transactions": transactions})


@login_required()
def transaction_detail(request):
    txid = request.GET.get("id")
    transaction = get_object_or_404(Transactions, unique_u=txid)
    txserializer = TnxSerializer(transaction)
    return JsonResponse({"transaction": txserializer.data})
    # return render(request, "useri/transactions.html", {"transaction": transaction})


@login_required()
def wallet_page(request):
    return render(request, "user/wallet.html")


@login_required()
def kyc_pge(request):
    user = request.user
    try:
        doc = Kyc.objects.get(user=request.user)
    except Kyc.DoesNotExist:
        doc = None
    if request.POST:
        form = KycForm(request.POST, request.FILES)
        if form.is_valid():
            if doc:
                document_front = form.cleaned_data["document_front"]
                document_back = form.cleaned_data["document_back"]
                doc.document_front = document_front
                doc.document_back = document_back
                doc.user = user
                doc.status = "proccessing"
                doc.save()
                messages.info(request, ("Document Submited"))
                return redirect("kyc")
            instance = form.save(commit=False)
            instance.user = user
            instance.save()
            messages.info(request, ("Document Submited"))
            return redirect("kyc")
    return render(request, "user/kyc.html", {"doc": doc})


@login_required()
def notifications_page(request):
    notifications = Notification.objects.filter(user=request.user).order_by("-date")
    return render(request, "user/notifications.html", {"notifications": notifications})


@login_required()
def investment_page(request):
    investments = Investments.objects.filter(user=request.user)
    return render(request, "user/investments.html", {"investments": investments})


@login_required()
def create_investment_page(request):
    user = request.user
    if user.is_verified != True:
        messages.error(request, "Verify Your Account")
        return redirect("kyc")
    if request.POST:
        pack_name = str((request.POST.get("pack_name"))).lower()
        amount = int(request.POST.get("amount"))
        package = get_object_or_404(Packages, name=pack_name)
        if amount >= package.min_amount or amount <= package.max_amount:
            if user.deposit_balance >= amount:
                investment = Investments(
                    user=user,
                    amount_invested=amount,
                    end_date=utils.get_deadline(package.duration),
                    package=package,
                )
                user.deposit_balance -= amount
                investment.save()
                user.save()
                messages.error(request, "Investment Created succesfully")
                return redirect("investment")
            else:
                messages.error(request, "Insuficient Funds Please Deposit")
                return redirect("investment")
        else:
            messages.error(
                request,
                "Please make sure the amount corresponds with the plans min and max amount",
            )
            return redirect("create-investment")

    return render(request, "user/create-investments.html")


@login_required()
def affiliate_page(request):
    return render(request, "user/affiliate.html")


@login_required()
def settings_page(request):
    user = request.user
    context = {
        "investment_count": Investments.objects.filter(user=user).count(),
    }
    if request.POST:
        form = UpdateUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            user.is_updated = True
            user.save()
            messages.error(request, "Account updated")
            return redirect("settings")
        else:
            messages.error(request, "Error in form field")
            return redirect("settings")
    return render(request, "useri/profile.html", context)


@login_required()
def settings_password_page(request):
    user = request.user
    if request.POST:
        form = ChangePasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.error(request, "Password Changed")
            return redirect("settings")
    else:
        messages.error(request, "GET REQUEST NOT ALLOWED")
        return redirect("settings")


@login_required()
def update_wallet_page(request):
    user = request.user
    try:
        paydetail = PaymenyDetails.objects.get(user=user)
    except PaymenyDetails.DoesNotExist:
        paydetail = None
    if request.POST:
        btc_address = request.POST.get("btc_address")
        usdt_address = request.POST.get("usdt_address")
        eth_address = request.POST.get("eth_address")
        if paydetail:
            paydetail.btc = btc_address
            paydetail.eth = eth_address
            paydetail.usdt = usdt_address

            paydetail.save()
        else:
            detaills = PaymenyDetails.objects.create(
                user=user,
                btc=btc_address,
                eth=eth_address,
                usdt=usdt_address,
            )
            detaills.save()

        messages.info(request, "Payments  details Updated succesfully")
        return redirect("update_wallet_page")

    return render(request, "useri/update_wallet.html", {"paydetail": paydetail})


@login_required()
def packages_view(request):
    return render(request, "useri/packages.html")


@login_required()
def change_password_view(request):
    user = request.user
    if request.POST:
        form = ChangePasswordForm(
            request.user,
            request.POST,
        )
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.info(request, "Password changed  successfully")
    else:
        form = ChangePasswordForm(user=user)
    return render(request, "useri/change_password.html", {"form": form})


@login_required()
def security_view(request):
    return render(request, "useri/security.html")


@login_required()
def enable_2fa(request):
    user = request.user

    otp_secret_key = utils.generate_totp_secret()
    # otp_secret_key = utils.generate_short_totp_secret()

    qr_code = utils.generate_qr_code(otp_secret_key, user)

    if request.POST:
        secret_key = request.POST.get("key")
        code = request.POST.get("code")

        totp = pyotp.TOTP(secret_key)

        if totp.verify(code):
            user.otp_secret_key = secret_key
            user.otp_enabled = True
            user.save()
            messages.info(request, "2FA has been activated")
            return redirect("enable_2fa")
        else:
            messages.info(request, "Code in invalid")
            return render(
                request,
                "useri/2fa.html",
                {"qr_code": qr_code, "otp_secret_key": secret_key},
            )

    return render(
        request,
        "useri/2fa.html",
        {"qr_code": qr_code, "otp_secret_key": otp_secret_key},
    )


@login_required()
def disable_2fa(request):
    user = request.user
    if request.POST:
        code = request.POST.get("code")
        totp = pyotp.TOTP(user.otp_secret_key)
        if totp.verify(code):
            user.otp_secret_key = ""
            user.otp_enabled = False
            user.save()
            messages.info(request, "2FA has been deactivated")
            return redirect("enable_2fa")
        else:
            messages.info(request, "code is invalid")
            return redirect("enable_2fa")
    messages.info(request, "SOMETHING WENT WRONG")
    return redirect("enable_2fa")
