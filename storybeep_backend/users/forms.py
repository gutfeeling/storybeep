from urllib.parse import urljoin

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UsernameField, AuthenticationForm
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import get_language
from django.core import signing
from django.urls import reverse
from django.contrib.sites.models import Site
from django.db import transaction
from django.conf import settings
from django.core.validators import EmailValidator
from django.template.loader import render_to_string
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
                     "placeholder" : _("Email"),
                     }
            ),
        validators = [
            EmailValidator(
                message = "Enter a valid email address e.g. email@example.com."
                ),
            ],
        )

    password = forms.CharField(
        label = _("Password"),
        strip = False,
        widget = forms.PasswordInput(
            attrs = {"placeholder" : _("Password")}
            )
        )

    def clean(self):

        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username is not None and password:

            try:

                user = StorybeepUser.objects.get(email = username)
                if not user.email_verified:
                    # need to include a send email verification link
                    self.add_error(
                        "username",
                        forms.ValidationError(
                            "This email is registered but has not been"
                            " verified."),
                        )
                else:
                    self.user_cache = authenticate(
                        username=username, password=password
                        )

                    if self.user_cache is None:
                        self.add_error(
                            "password",
                            forms.ValidationError("Wrong password."),
                            )
                    else:
                        self.confirm_login_allowed(self.user_cache)

            except StorybeepUser.DoesNotExist:
                self.add_error(
                    "username",
                    forms.ValidationError(
                        "This account is not registered with us."),
                    )

        return self.cleaned_data



class SignupForm(forms.Form):

    error_css_class = "error"

    email = forms.EmailField(
        widget = forms.TextInput(
            attrs = {"placeholder" : _("Email")}
            ),
        error_messages = {
            "invalid" : "Enter a valid email address e.g. email@example.com."
            }
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
            if user.email_verified:
                raise forms.ValidationError("This account already exists.")
            else:
                return email
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

            language = get_language()

            try:
                # this block runs if we have an user who is in the database
                # but not verified. in this case, we repeat the sign up
                # process, changing the password to the new one.
                new_user = StorybeepUser.objects.get(email = email)
                new_user.set_password(password)
                new_user.save()

                settings = new_user.settings
                settings.language = language
                settings.save()

            except StorybeepUser.DoesNotExist:
                # this is what usually happens
                new_user = StorybeepUser.objects.create_user(email, password)

                # set default settings for the user

                new_user_settings = Settings(
                    user = new_user, language = language
                    )
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

        # change http to https at some point
        storybeep_logo_url = ("http://{0}/static/images/"
            "storybeep_logo.png".format(domain))

        text_message = render_to_string("activation_email.txt",
            {"link_absolute" : link_absolute}
            )

        html_message = render_to_string("activation_email.html",
            {"storybeep_logo_url" : storybeep_logo_url,
             "activation_url" : link_absolute,
             }
            )

        try:
            mailer = settings.MAILER
        except AttributeError:
            raise ImproperlyConfigured("Please set the MAILER settings.")

        django_rq.enqueue(
            user.send_email,
            subject = "Activate your Storybeep account.",
            message = text_message,
            html_message = html_message,
            from_email = "Storybeep <{0}>".format(mailer),
            )


class PublisherSignupForm(forms.Form):

    password = forms.CharField(
        widget = forms.PasswordInput(
            attrs = {"placeholder" : _("Create a password")}
            )
        )

    def save(self, email, language, name):
        password = self.cleaned_data["password"]

        with transaction.atomic():

            new_user = StorybeepUser.objects.create_user(email, password)
            new_user.is_publisher = True
            new_user.email_verified = True
            new_user.save()

            new_user_settings = Settings(
                user = new_user, language = language, name = name
                )
            new_user_settings.save()

        return new_user


class SettingsForm(forms.Form):

    language = forms.ChoiceField(choices = settings.LANGUAGES)

    def save(self, user):

        settings = user.settings
        settings.language = self.cleaned_data["language"]
        settings.save()

        return settings
