from rest_framework.views import APIView
from rest_framework.response import Response
from .serializer import RegisterSerializer
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.utils.encoding import force_str
from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)


from django.core.cache import cache
from account.models import Account
from baseapp import utils


class SignUpView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        # uidb64 = request.GET.get("authToken")
        # if uidb64:
        #     ke_y = force_str(urlsafe_base64_decode(uidb64))
        #     data = cache.get(ke_y)
        #     if data:
        #         return Response(data)
        #     else:
        #         return Response({"error": "Link is invalid!"})
        # else:
        #     return Response({"error": "Link is invalid"})

        accounts = Account.objects.all()
        emails = [account.email for account in accounts if account.email]
        usernames = [account.username for account in accounts if account.username]

        return Response({"emails": emails, "usernames": usernames})

    def post(self, request, format=None):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            current_site = get_current_site(request)
            subject = f"welcome , confirm your email address"
            user = {
                "email": serializer.data["email"],
                "password": serializer.data["password"],
                "fullname": serializer.data["fullname"],
                "username": serializer.data["username"],
                "phone": serializer.data["phone"],
            }
            ke_y = f"register-{user['email']}"
            item = cache.get(ke_y)
            if item:
                cache.delete(ke_y)
            cache.set(ke_y, user, timeout=600)
            context = {
                "user": user,
                "domain": current_site.domain,
                "token": urlsafe_base64_encode(force_bytes(ke_y)),
            }
            message = get_template("account/confirmation.email.html").render(context)
            mail = EmailMessage(
                subject=subject,
                body=message,
                from_email=utils.EMAIL_ADMIN,
                to=[user["email"]],
                reply_to=[utils.EMAIL_ADMIN],
            )
            mail.content_subtype = "html"
            mail.send(fail_silently=True)

            return Response({"msg": "Successful"})
        else:
            return Response(serializer.errors)


# next is making it so when user click the link in the email it would
# redirect them to a page that will process the user data and save it
