from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from account.models import Kyc

from baseapp import utils
from users.models import Notification, Transactions, Packages, Investments
from .forms import DepositForm, KycForm, UpdateUserForm
from django.contrib.auth.forms import PasswordChangeForm


@login_required()
def index(request):
    user = request.user
    context = {
        "investment_count": Investments.objects.filter(user=user).count(),
    }
    return render(request, "user/profileii.html", context)


@login_required()
def deposit_page(request):
    if request.POST:
        amount = int(request.POST.get("amount"))
        method = request.POST.get("mode")
        return redirect("deposit_confrim", amount=amount, mode=method)
    return render(request, "user/deposit.html")


@login_required()
def deposit_confrim(request, amount, mode):
    user = request.user
    if mode in utils.wallets and amount >= 700:
        if request.POST:
            form = DepositForm(request.POST, request.FILES)
            if form.is_valid():
                instance = form.save(commit=False)
                instance.user = user
                form.save()
                utils.create_notification(
                    model=Notification,
                    user=user,
                    title="Deposit successfull",
                    body=f"You just made a deposit of ${amount}",
                )
                messages.error(request, "Deposit created")

                return redirect("deposit_page")
        else:
            context = {
                "amount": amount,
                "mode": mode,
                "address": utils.ADMIN_ADDRESS[mode],
            }
            return render(request, "user/deposit-confirm.html", context)

    else:
        messages.error(request, "Invalid Link")
        return redirect("deposit_page")


@login_required()
def withdrawal(request):
    user = request.user
    if user.is_verified != True:
        messages.error(request, "Verify Your Account")
        return redirect("kyc")

    if request.POST:
        amount = int(request.POST.get("amount"))
        amount_in_coin = request.POST.get("amount_in_coin")
        mode = request.POST.get("mode")
        addr = utils.check_user_address(user)
        if addr:
            if user.balance >= amount:
                transaction = Transactions(
                    user=user,
                    amount=amount,
                    amount_in_coin=amount_in_coin,
                    method=mode,
                    trans_type=utils.W,
                )
                user.balance -= amount
                user.save()
                transaction.save()
                utils.create_notification(
                    model=Notification,
                    user=user,
                    title="withdrawal successfull",
                    body=f"You just place a withdrawal of ${amount}",
                )
                messages.error(request, "Transaction succesful")
                return redirect("withdrawal")
            else:
                messages.error(request, "Insuficient Funds")
                return redirect("withdrawal")
        else:
            messages.error(request, "Please Update your withdrawal addresses")
            return redirect("withdrawal")
    return render(request, "user/withdrawal.html")


@login_required()
def transactions_page(request):
    transactions = Transactions.objects.filter(user=request.user)
    return render(request, "user/transactions.html", {"transactions": transactions})


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
        "form_password": PasswordChangeForm(user),
    }
    if request.POST:
        form = UpdateUserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            utils.create_notification(
                model=Notification,
                user=user,
                title="Account updated",
                body=f"You just updated your account",
            )
            messages.error(request, "Account updated")
            return redirect("settings")
        else:
            messages.error(request, "Error in form field")
            return redirect("settings")
    return render(request, "user/profilei.html", context)


@login_required()
def settings_password_page(request):
    user = request.user
    if request.POST:
        form = PasswordChangeForm(user, request.POST)
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
    if request.POST:
        btc_address = request.POST.get("btc_address")
        usdt_address = request.POST.get("usdt_address")
        eth_address = request.POST.get("eth_address")

        user.eth_address = eth_address
        user.usdt_address = usdt_address
        user.btc_address = btc_address

        user.save()
        messages.error(request, "Wallet Updated succesfully")
        return redirect("update_wallet_page")

    return render(request, "user/update_wallet.html")
