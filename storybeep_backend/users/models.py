from urllib.parse import urljoin

from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.sites.models import Site
from django.urls import reverse
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from utils.sign import get_hmac_code

class StorybeepUserManager(BaseUserManager):

    def create_user(self, email, password=None):

        user = self.model(email=email)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        # We are not using the Django Admin interface. We use the shell
        # (python manage.py shell) instead. Therefore,
        # we don't need superusers.

        pass


class StorybeepUser(AbstractBaseUser):

    """See https://docs.djangoproject.com/en/1.10/topics/auth/customizing/#specifying-custom-user-model
    """

    email = models.EmailField(unique=True)

    # We have two classes of users: publishers and readers. The
    # is publisher flag indicates if an user is a publisher.
    is_publisher = models.BooleanField(default = False)

    # The email_verified flag indicates if the email of the user
    # has been verified.
    email_verified = models.BooleanField(default = False)

    # Email is the unique identifying field for a Storybeep user.
    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = []

    objects=StorybeepUserManager()

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email

    def send_email(self, subject, message, from_email):
        """
        Sends an email to the user using the django.core.mail module
        """
        send_mail(
            subject = subject,
            message = message,
            from_email = from_email,
            recipient_list = [self.email],
            fail_silently = False,
            )

class VerifiedPublisher(models.Model):
    """ Publisher signup is invitation-only. To send an invitation, we add a
    publisher's email to this table, which automatically sends an invitation
    email to the publisher with a signed link. When the publisher clicks the
    link, he is redirected to the signup page, where he needs to enter
    a password to secure his account. As soon as he provides the password,
    he can start using his account.
    """
    email = models.EmailField(unique=True)
    language = models.CharField(max_length = 10, choices = settings.LANGUAGES)

    def save(self, *args, **kwargs):
        """ We override the save method to automatically send an invitation
        email when we add an email to this table.
        """
        self.send_invitation_email()
        super(VerifiedPublisher, self).save(*args, **kwargs)

    def send_invitation_email(self):
        """ Send an invitation email """

        hmac_code = get_hmac_code(self.email)

        link_relative = reverse(
            "verify_email_and_publisher_signup_view",
            kwargs = {"hmac_code" : hmac_code},
            )

        # get the root domain using the Django sites framework to form
        # the absolute url

        current_site = Site.objects.get_current()
        domain = current_site.domain

        # should change this to https when we add ssl to our site
        # see https://code.djangoproject.com/ticket/26079

        link_absolute = urljoin("http://" + domain, link_relative)

        try:
            mailer = settings.MAILER
        except AttributeError:
            raise ImproperlyConfigured("Please set the MAILER settings.")

        send_mail(
            subject = "Invitation from Storybeep",
            message = link_absolute,
            from_email = mailer,
            recipient_list = [self.email],
            fail_silently = False,
            )

    def __str__(self):
        return self.email


class Settings(models.Model):

    user = models.OneToOneField(StorybeepUser)
    # how many characters do we actually need?
    language = models.CharField(max_length = 10, choices = settings.LANGUAGES)

    def __str__(self):
        return "user: {0} language: {1}".format(self.user.email,
            self.language)
