import json
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
import pyotp
from .forms import RegisterForm, LoginForm, SetPasswordForm
from django.contrib.auth.forms import SetPasswordForm
from baseapp import utils
from .models import Account, LoginHistory
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from baseapp import utils
from django.http import HttpResponseRedirect


# def home(request):
#     return HttpResponseRedirect("https://app.wealthlines.org")


def login_re(request):
    return HttpResponseRedirect("http://localhost:5173/login/")


def register_re(request):
    return HttpResponseRedirect("http://localhost:5173/register/")


def sign_out(request):
    logout(request)
    return HttpResponseRedirect("http://localhost:5173/login/")


def empty_page(request):
    # return HttpResponseRedirect("localhost:5173/sign-up/")
    return render(request, "account/verif-email.html")


@csrf_exempt
def verify_otp(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            userid = data.get("userid")
            code = data.get("code")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"})

        if not userid or not code:
            return JsonResponse({"error": "User ID and code are required"})

        try:
            user = Account.objects.get(pk=int(userid))
        except (Account.DoesNotExist, ValueError, TypeError):
            return JsonResponse(
                {"error": "User not found or invalid User ID"}, status=404
            )

        totp = pyotp.TOTP(user.otp_secret_key)
        if totp.verify(code):
            return JsonResponse({"msg": "Success"})
        else:
            return JsonResponse({"error": "Code is invalid"})
    return JsonResponse({"error": "GET request not allowed"}, status=405)


def loginUser(request):
    token = request.GET.get("token")
    if token:
        ke_y = force_str(urlsafe_base64_decode(token))
        data = cache.get(ke_y)
        if data:
            print(data)
            try:
                account = authenticate(
                    request, email=data["email"], password=data["password"]
                )
                login(request, account)
                LoginHistory.objects.create(
                    user=account,
                    log_ip=utils.get_client_ip(request),
                )
                cache.delete(ke_y)
                messages.info(request, "Logged In")
                return redirect("dashboard")
            except:
                messages.info(
                    request,
                    "Something went wrong try again !",
                )
                return redirect("empty_page")
        else:
            messages.info(
                request,
                "Something went wrong ",
            )
            return redirect("empty_page")
    else:
        messages.info(
            request,
            "Something went wrong try again",
        )
        return redirect("empty_page")


def account_activate_view(request):
    token = request.GET.get("token")
    if not token:
        messages.info(request, "The confirmation link is invalid")
        return redirect("empty_page")
    else:
        email = force_str(urlsafe_base64_decode(token))
        user = cache.get(email)
        if user:
            cache.delete(user["email"])
            account = Account(
                email=user["email"],
                fullname=user["fullname"],
                username=user["username"],
                phone=user["phone"],
            )
            account.set_password(user["password"])
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
