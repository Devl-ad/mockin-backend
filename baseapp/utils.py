import random
from django.conf import settings
from django.utils import timezone
import qrcode
from io import BytesIO
import string
from django.core.mail import EmailMessage
from django.template.loader import get_template

import pyotp

from base64 import b64encode

from datetime import timedelta
from uuid import uuid4

# from users.models import Notification


EMAIL_ADMIN = settings.DEFAULT_FROM_EMAIL
D = "deposit"
W = "withdraw"

ADMIN_ADDRESS = {
    "BTC": "18gTvDGzJKW9N1ovMh6pL77d7eGDRnHnCj",
    "ETH": "0xF3f2136F6e34CB413e3887B978fD3015a1EECC4a",
    "USDT": "0xF3f2136F6e34CB413e3887B978fD3015a1EECC4a",
}
wallets = ["BTC", "ETH", "USDT"]


def gen_random_number():
    return str(random.randint(100000, 999999))


def rand_code():
    code = str(uuid4()).replace(" ", "-").upper()[:6]
    return code


def generate_short_totp_secret():
    return "".join(random.choices(string.ascii_uppercase + "234567", k=8))


def generate_totp_secret():
    return pyotp.random_base32()


def generate_qr_code(secret, user):
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        user.username, issuer_name="Wealth line"
    )

    img = qrcode.make(totp_uri)
    buffer = BytesIO()
    img.save(buffer)
    buffer.seek(0)
    encoded_img = b64encode(buffer.read()).decode()
    qr_code = f"data:image/png;base64,{encoded_img}"
    return qr_code


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[-1].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def get_deadline(days):
    return timezone.now() + timedelta(days=days)


def send_mail(subject, context, to_email, template):
    message = get_template(template).render(context)
    mail = EmailMessage(
        subject=subject,
        body=message,
        from_email=EMAIL_ADMIN,
        to=to_email,
        reply_to=[EMAIL_ADMIN],
    )
    mail.content_subtype = "html"
    mail.send(fail_silently=True)
