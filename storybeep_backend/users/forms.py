from urllib.parse import urljoin

from django import forms
from django.contrib.auth.forms import UsernameField, AuthenticationForm
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import get_language
from django.core import signing
from django.urls import reverse
from django.contrib.sites.models import Site
from django.db import transaction
from django.conf import settings
import django_rq

# not using get_user_model() because this unnecessarily obfuscates code
# by referring to email as username.
from users.models import StorybeepUser, Settings
from utils.sign import get_hmac_code


class LoginForm(AuthenticationForm):
    """Using a custom login form to add placeholder texts to the form fields
    and to return custom form validation errors."""

    username = UsernameField(
        max_length = 254,
        widget = forms.TextInput(
            attrs = {"autofocus" : True,
                     "placeholder" : _("Your Email"),
                     }
            )
        )

    password = forms.CharField(
        label = _("Password"),
        strip = False,
        widget = forms.PasswordInput(
            attrs = {"placeholder" : _("Password")}
            )
        )

    def clean_username(self):
        """Raise error if the email has not been verified"""

        email = self.cleaned_data["username"]
        try:
            user = StorybeepUser.objects.get(email = email)
            if not user.email_verified:
                # need to include a send email verification link
                raise forms.ValidationError("Email is not verified.")
        except StorybeepUser.DoesNotExist:
            pass
        return email


class SignupForm(forms.Form):

    email = forms.EmailField(
        widget = forms.TextInput(
            attrs = {"placeholder" : _("Your Email")}
            )
        )

    password = forms.CharField(
        widget = forms.PasswordInput(
            attrs = {"placeholder" : _("Password")}
            )
        )

    def clean_email(self):
        """Raise error if user with the submitted email does not exist"""

        email = self.cleaned_data["email"]
        try:
            user = StorybeepUser.objects.get(email = email)
            raise forms.ValidationError("User exists.")
        except StorybeepUser.DoesNotExist:
            return email

    def save(self):
        """Creates the user in the database, sends a email with a
        verification link to the user and returns the user instance"""

        email = self.cleaned_data["email"]
        password = self.cleaned_data["password"]

        with transaction.atomic():
            # Using atomic transaction to destroy the user if the
            # email with verification link could not be sent.
            # This ensures that another sign up attempt will not
            # into an error because the user exists.

            # we should actually use signals to send the email
            # and give the user the resend option.
            new_user = StorybeepUser.objects.create_user(email, password)

            # set default settings for the user
            language = get_language()
            new_user_settings = Settings(user = new_user, language = language)
            new_user_settings.save()

            self.send_verification_email(new_user)

        return new_user

    def send_verification_email(self, user):

        hmac_code = get_hmac_code(user.email)

        link_relative = reverse(
            "verify_email_view",
            kwargs = {"hmac_code" : hmac_code},
            )

        current_site = Site.objects.get_current()
        domain = current_site.domain

        link_absolute = urljoin("http://" + domain, link_relative)

        try:
            mailer = settings.MAILER
        except AttributeError:
            raise ImproperlyConfigured("Please set the MAILER settings.")

        django_rq.enqueue(
            user.send_email,
            subject = "Verify your email.",
            message = link_absolute,
            from_email = mailer,
            )


class PublisherSignupForm(forms.Form):

    password = forms.CharField(
        widget = forms.PasswordInput(
            attrs = {"placeholder" : _("Password")}
            )
        )

    def save(self, email, language):
        password = self.cleaned_data["password"]

        with transaction.atomic():

            new_user = StorybeepUser.objects.create_user(email, password)
            new_user.is_publisher = True
            new_user.email_verified = True
            new_user.save()

            new_user_settings = Settings(user = new_user, language = language)
            new_user_settings.save()

        return new_user
