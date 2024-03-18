from django.urls import path
from . import views
from .api import views as api_view

urlpatterns = [
    path("register/", api_view.SignUpView.as_view(), name="register"),
    path("sign-out/", views.sign_out, name="sign-out"),
    path("empty-page/", views.empty_page, name="empty_page"),
    path("reset-password/", views.reset_password, name="reset-password"),
    path("verify-email/", views.account_activate_view, name="activate"),
    path("new-password/<uidb64>/", views.new_password_view, name="new-password"),
]
