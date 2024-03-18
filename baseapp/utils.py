import random
from django.conf import settings
from django.utils import timezone


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