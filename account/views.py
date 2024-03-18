from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import login, authenticate, logout

from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.utils.encoding import force_str
from .forms import RegisterForm, LoginForm, SetPasswordForm
from django.contrib.auth.forms import SetPasswordForm
from baseapp import utils
from .models import Account
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from baseapp import utils
from django.http import HttpResponseRedirect


def sign_out(request):
    logout(request)
    return redirect("sign-in")


def empty_page(request):
    # return HttpResponseRedirect("localhost:5173/sign-up/")
    return render(request, "account/verif-email.html")


def account_activate_view(request):
    token = request.GET.get("token")
    if not token:
        messages.info(request, "SOMETHING WENT WRONG")
        return redirect("empty_page")
    else:
        email = force_str(urlsafe_base64_decode(token))
        user = cache.get(email)
        if user:
            cache.delete(user["email"])
            account = Account(
                email=user["email"],
                first_name=user["first_name"],
                last_name=user["last_name"],
            )
            account.set_password(user["password1"])
            account.save()
            login(request, account)
            messages.info(request, "Account created SuccessFully")
            return redirect("dashboard")
        else:
            messages.info(
                request,
                "The confirmation link is invalid, possibly because it has already expired",
            )
            return redirect("empty_page")


def reset_password(request):
    if request.POST:
        email = request.POST.get("email")
        try:
            account = Account.objects.get(email__exact=email)
        except Account.DoesNotExist:
            account = None
        if account:
            ke_y = cache.get(account.username)
            if ke_y:
                cache.delete(account.username)
            cache.set(account.username, account, timeout=300)
            current_site = get_current_site(request)
            subject = "Reset Your Password"
            context = {
                "user": account,
                "domain": current_site.domain,
                "uid": urlsafe_base64_encode(force_bytes(account.email)),
            }
            message = get_template("auth/resetpassword.email.html").render(context)
            mail = EmailMessage(
                subject=subject,
                body=message,
                from_email=utils.EMAIL_ADMIN,
                to=[account.email],
                reply_to=[utils.EMAIL_ADMIN],
            )
            mail.content_subtype = "html"
            mail.send(fail_silently=True)

            messages.success(
                request, (" check your mail box for instructions to continue")
            )
            return redirect("reset-password")

        else:
            messages.success(request, ("A User with this email does't exist"))
            return redirect("reset-password")
    return render(request, "auth/reset-password.html")


def new_password_view(
    request,
    uidb64,
):
    email = force_str(urlsafe_base64_decode(uidb64))

    account = utils.check_user(email, Account)
    user = cache.get(account.username)
    if user and account is not None:
        if request.POST:
            form = SetPasswordForm(account, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, ("Your Password has been reset"))
                return redirect("sign-in")

        else:
            form = SetPasswordForm(user=account)
            return render(request, "auth/new-password.html", {"form": form})
    else:
        messages.success(request, ("Invalid Link"))
        return redirect("reset-password")
