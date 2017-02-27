from django.conf.urls import url, include
from django.contrib.auth import views as auth_views

from .views import (
    SignupView, SignupSuccessfulView, VerifyEmailView,
    EmailVerificationFailedView, PublisherSignupView,
    EmailAlreadyVerifiedView,
    )

from .forms import LoginForm

urlpatterns = [
    url(
        regex  = r"^signup/$",
        view = SignupView.as_view(),
        name = "signup_view",
        ),
    url(
        r"^signup-successful/$",
        SignupSuccessfulView.as_view(),
        name = "signup_successful_view",
    ),
    url(
        r"^verify-email/(?P<hmac_code>.+)/$",
        VerifyEmailView.as_view(),
        name = "verify_email_view",
    ),
    #need a send-verification-email view
    url(
        r"^verify-email-and-publisher-signup/(?P<hmac_code>.+)/$",
        PublisherSignupView.as_view(),
        name = "verify_email_and_publisher_signup_view",
    ),
    url(
        r"^email_verification-failed/$",
        EmailVerificationFailedView.as_view(),
        name = "email_verification_failed_view",
    ),
    url(
        r"^email-already-verified/$",
        EmailAlreadyVerifiedView.as_view(),
        name = "email_already_verified_view",
    ),

    #https://docs.djangoproject.com/en/1.10/topics/auth/default/#module-django.contrib.auth.views
    url(
        regex = r"^login/$",
        view = auth_views.login,
        kwargs = {
            "template_name": "login.html",
            "authentication_form" : LoginForm,
            },
        name= "login_view",
    ),
    url(
        r"^logout/$",
        auth_views.logout,
        name = "logout_view",
    ),
    ]
