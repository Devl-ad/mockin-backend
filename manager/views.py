from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import login, logout
from account.models import Kyc, PaymenyDetails
from users.models import Transactions, Investments, Notification
from django.db.models import Sum

# from users.forms import WalletForm
from baseapp import utils
from .decorator import manager_required

Account = get_user_model()


@manager_required
def dashboard(request):
    total_earnings = 0
    investments = Investments.objects.all()
    for invest in investments:
        total_earnings += invest.amount_invested
    am_deposit = 0
    am_withdraw = 0
    for obj in Transactions.objects.filter(status="approved"):
        if obj.trans_type == utils.D:
            am_deposit += obj.amount
        elif obj.trans_type == utils.W:
            am_withdraw += obj.amount

    context = {
        "earnings": total_earnings,
        "am_deposit": am_deposit,
        "am_withdraw": am_withdraw,
        "users": Account.objects.all().count(),
        "withdrawal": Transactions.objects.filter(trans_type=utils.W).count(),
        "deposit": Transactions.objects.filter(trans_type=utils.D).count(),
        "withdrawal_pending": Transactions.objects.filter(
            trans_type=utils.W, status="pending"
        ).count(),
        "deposit_pending": Transactions.objects.filter(
            trans_type=utils.D, status="pending"
        ).count(),
    }
    return render(request, "superadmin/dashboard.html", context)


@manager_required
def users(request):
    users = Account.objects.all().order_by("last_login")
    return render(request, "superadmin/users.html", {"users": users})


@manager_required
def user_detail(request, pk):
    account = get_object_or_404(Account, pk=pk)

    investment = Investments.objects.filter(user=account)

    tot_amount_invested = (
        Investments.objects.filter(user=account).aggregate(Sum("amount_invested"))[
            "amount_invested__sum"
        ]
        or 0
    )

    if request.POST:
        amount = int(request.POST.get("amount"))
        submit = request.POST.get("submit")
        if submit == "Top up":
            transaction = Transactions.objects.create(
                user=account,
                amount=amount,
                trans_type=utils.D,
                status="approved",
                method="admin",
                unique_u=utils.rand_code(),
            )
            account.balance += amount
            account.save()

            current_site = get_current_site(request)
            subject = "Account Deposited"
            context = {
                "user": account,
                "domain": current_site.domain,
                "amount": amount,
                "transaction": transaction,
            }

            utils.send_mail(
                subject,
                context,
                [transaction.user.email],
                "superadmin/invoice.email.html",
            )

            messages.success(request, "Account Top Up Successful")
            return redirect("user_detail", pk=account.id)
        else:
            messages.warning(request, "UNKNOWN ERROR OCCURED")
            return redirect("user_detail", pk=account.id)

    return render(
        request,
        "superadmin/user_detail.html",
        {
            "account": account,
            "investment": investment,
            "tot_amount_invested": tot_amount_invested,
        },
    )


@manager_required
def withdrawal_(request):
    """
    LIST ALL WITHDRAWAL
    """
    transactions = Transactions.objects.filter(trans_type=utils.W).order_by("-date")
    return render(request, "superadmin/withdrawal.html", {"transactions": transactions})


def login_user_account(request, pk):
    """
    LOG IN USER ACCOUNT
    """
    logout(request)
    user = Account.objects.get(pk=pk)
    login(request, user)
    messages.success(request, f"Logged In As {user.username}")
    return redirect("dashboard")


@manager_required
def withdrawal_detail(request, pk):
    """
    GET DETAILS OF A  WITHDRAWAL
    """
    try:
        transaction = Transactions.objects.get(pk=pk)
        paydetail = get_object_or_404(PaymenyDetails, user=transaction.user)

        address = "btc"
    except Transactions.DoesNotExist:
        transaction = None
        return redirect("withdrawal_")
    if request.POST:
        submit = request.POST.get("submit")
        if submit == "decline":
            reason = request.POST.get("reason")
            transaction.status = "declined"
            transaction.reason = reason
            transaction.user.balance += transaction.amount
            transaction.user.save()
            transaction.save()

            current_site = get_current_site(request)
            subject = "Withdrawal Declined"
            context = {
                "status": "declined",
                "domain": current_site.domain,
                "transaction": transaction,
            }
            utils.send_mail(
                subject,
                context,
                [transaction.user.email],
                "superadmin/invoice.email.html",
            )

            messages.warning(request, "Withdrawal declined")
            return redirect("withdrawal_detail", pk=transaction.pk)

        elif submit == "approve":
            transaction.status = "approved"
            transaction.user.total_withdraw += transaction.amount
            transaction.user.save()
            transaction.save()

            current_site = get_current_site(request)
            subject = "Withdrawal Approved"
            context = {
                "status": "approved",
                "domain": current_site.domain,
                "transaction": transaction,
            }
            utils.send_mail(
                subject,
                context,
                [transaction.user.email],
                "superadmin/invoice.email.html",
            )

            messages.success(request, "Withdrawal Approved")
            return redirect("withdrawal_detail", pk=transaction.pk)

        else:
            messages.success(request, "UNKNOWN ERROR OCCURED")
            return redirect("withdrawal_detail", pk=transaction.pk)

    return render(
        request,
        "superadmin/withdrawal_detail.html",
        {
            "transaction": transaction,
            "paydetail": paydetail.get_cryptocurrency_field(transaction.method.lower()),
        },
    )


@manager_required
def deposit_(request):
    """
    LIST ALL DEPOSIT
    """
    transactions = Transactions.objects.filter(trans_type=utils.D).order_by("-date")
    return render(request, "superadmin/deposit.html", {"transactions": transactions})


@manager_required
def deposit_details(request, pk):
    transaction = get_object_or_404(Transactions, pk=pk)
    if request.POST:
        submit = request.POST.get("submit")
        if submit == "decline":
            reason = request.POST.get("reason")
            transaction.reason = reason
            transaction.status = "declined"
            transaction.save()
            current_site = get_current_site(request)
            subject = "Deposit Declined"
            context = {
                "status": "declined",
                "domain": current_site.domain,
                "transaction": transaction,
            }
            utils.send_mail(
                subject,
                context,
                [transaction.user.email],
                "superadmin/invoice.email.html",
            )

            messages.warning(request, "Deposit declined")
            return redirect("deposit_details", pk=transaction.pk)

        elif submit == "approve":
            transaction.status = "approved"
            transaction.user.deposit_balance += transaction.amount
            transaction.user.save()
            transaction.save()

            current_site = get_current_site(request)
            subject = "Deposited Approved"
            context = {
                "status": "approved",
                "domain": current_site.domain,
                "transaction": transaction,
            }
            utils.send_mail(
                subject,
                context,
                [transaction.user.email],
                "superadmin/invoice.email.html",
            )

            messages.success(request, "Account Deposit Successful")
            return redirect("deposit_details", pk=transaction.id)
    return render(
        request, "superadmin/deposit_details.html", {"transaction": transaction}
    )


@manager_required
def documents_(request):
    kyc = Kyc.objects.all()
    return render(request, "superadmin/doc.html", {"kyc": kyc})


@manager_required
def documents_details(request, pk):
    kyc = get_object_or_404(Kyc, pk=pk)
    return render(request, "superadmin/doc_detail.html", {"kyc": kyc})


@manager_required
def process_documents_(request, pk):
    if request.POST:
        doc = Kyc.objects.get(pk=pk)
        action = request.POST.get("action")
        if action == "Approve":
            doc.status = "approved"
            doc.user.is_verified = True
            doc.user.save()
            utils.create_notification(
                model=Notification,
                user=doc.user,
                title="KYC Approved",
                body=f"Your account has been verified",
            )
        elif action == "Decline":
            doc.status = "declined"
            utils.create_notification(
                model=Notification,
                user=doc.user,
                title="KYC Declined",
                body=f"Your kyc was declined try again",
            )
        else:
            messages.success(request, "Error")
            return redirect("docs_details", pk=doc.id)
        doc.save()
        messages.success(request, action)
        return redirect("docs_details", pk=doc.id)
    else:
        return JsonResponse({"msg": "GET REQUST NOT ACCEPTED"})


@manager_required
def investments(request):
    """
    GET LIST OF A  INVESTMENTS
    """
    investments = Investments.objects.all().order_by("-date")
    return render(request, "superadmin/investments.html", {"investments": investments})


@manager_required
def investments_detail(request, pk):
    """
    GET DETAILS OF A  INVESTMENTS
    """
    try:
        investment = Investments.objects.get(pk=pk)
    except Investments.DoesNotExist:
        investment = None
        messages.success(request, f"UNKNOW ERROR OCCURED")
        return redirect("investments")
    if request.POST:
        if investment.status != "completed":
            # investment.user.balance += investment.amount_earn
            investment.status = "completed"
            # investment.user.save()
            investment.save()

        messages.success(request, f"Investment completed")
        return redirect("investments_detail", pk=pk)

    else:
        return render(
            request, "superadmin/investment_detail.html", {"investment": investment}
        )


@manager_required
def investments_topup(request):
    if request.POST:
        invest_pk = request.POST.get("invest_id")
        amount = int(request.POST.get("amount"))

        investment = get_object_or_404(Investments, pk=invest_pk)

        investment.amount_earn += amount
        investment.user.balance += amount
        investment.user.save()
        investment.save()

        messages.info(request, "Toped up successfull")
        return redirect("investments_detail", pk=invest_pk)
    else:
        messages.info(request, "Not Found")
        return redirect("investments")


# @manager_required
# def change_wallet(request):
#     wallet = get_object_or_404(Wallet, pk=1)
#     if request.POST:
#         form = WalletForm(request.POST, instance=wallet)
#         if form.is_valid():
#             form.save()
#             messages.info(request, "Wallet adress has been updated")
#             return redirect("change-addr")
#     else:
#         form = WalletForm(instance=wallet)
#     return render(request, "superadmin/wallet_addr.html", {"form": form})
