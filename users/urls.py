from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.index, name="dashboard"),
    path("deposit-funds/", views.deposit_page, name="deposit_page"),
    path(
        "confirm-deposit/<int:amount>/<str:mode>/",
        views.deposit_confrim,
        name="deposit_confrim",
    ),
    path("withdraw-funds/", views.withdrawal, name="withdrawal"),
    path("transactions-log/", views.transactions_page, name="transactions"),
    path("wallet/", views.wallet_page, name="wallet"),
    path("kyc/", views.kyc_pge, name="kyc"),
    path("notifications/", views.notifications_page, name="notifications"),
    path("investments/", views.investment_page, name="investment"),
    path("create-investments/", views.create_investment_page, name="create-investment"),
    path("affiliate/", views.affiliate_page, name="affiliate"),
    path("settings/", views.settings_page, name="settings"),
    path("set-password/", views.settings_password_page, name="settings_password_page"),
    path("update-wallet-address/", views.update_wallet_page, name="update_wallet_page"),
]
