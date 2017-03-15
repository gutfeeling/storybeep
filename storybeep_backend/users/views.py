from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.contrib.auth import login
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin

from storybeep_backend.views import SessionMixin, CommonContextMixin
from utils.sign import validate_code
from utils.language import set_language_in_session
from .models import StorybeepUser, VerifiedPublisher
from .forms import SignupForm, PublisherSignupForm, SettingsForm


class PublisherOnlyAccessMixin(UserPassesTestMixin):
    """Add this mixin as the leftmost parent class of any view that should
    only be accessed by a publisher. Users who are not logged in will
    be redirected to the login page. Users of the "reader" type will
    get a HTTP 403 Forbidden response.
    """

    login_url = reverse_lazy("login_view")

    permission_denied_message = """Only publishers are allowed to access this
        page or perform this action. Please log in with a verified publisher
        account.
        """

    def test_func(self):
        user = self.request.user
        if user.is_authenticated:
            if not user.is_publisher:
                self.raise_exception = True
            return user.is_publisher
        else:
            return False


class ReaderOnlyAccessMixin(UserPassesTestMixin):
    """Add this mixin as the leftmost parent class of any view that should
    only be accessed by a reader. Users who are not logged in will
    be redirected to the login page. Users of the "publisher" type will
    get a HTTP 403 Forbidden response.
    """

    login_url = reverse_lazy("login_view")

    permission_denied_message = """Publishers are not allowed to access this
        page or perform this action. Please log in with a non publisher
        account.
        """

    def test_func(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_publisher:
                self.raise_exception = True
            return not user.is_publisher
        else:
            return False


class SignupView(SessionMixin, FormView):
    """On a get request, return the signup page. On a post request, create
    the user and send an email with the verification link
    """

    template_name = "signup.html"
    form_class = SignupForm

    #reverse_lazy should be used for the url attributes of generic
    #class based views
    #https://docs.djangoproject.com/en/1.11/ref/urlresolvers/#reverse-lazy
    success_url = reverse_lazy("signup_successful_view")

    def form_valid(self, form):

        new_user = form.save()

        # set the language preference of the user's session based on
        # the user's default settings

        language = new_user.settings.language
        set_language_in_session(language, self.request.session)

        # this ensures the user automatically  starts tracking the story in
        # the landing page after the sign up process is complete.
        self.track_stories_from_session_data(new_user)

        return super(SignupView, self).form_valid(form)


class SignupSuccessfulView(TemplateView):
    """Return a page that informs that the signup was successful and that an
    email with a verification link has been sent.
    """

    template_name = "signup_successful.html"


class VerifyEmailView(RedirectView):
    """This view results from clicking the link in the verification email.
    It sets the email_verified flag to True, logs the user in and
    redirects to the home page of the user
    """

    def get_redirect_url(self, *args, **kwargs):

        user = self.get_user()

        if user is not None:
            if user.email_verified:
                # happens when you click the verification link the second time
                # this view should have a log in button
                return reverse_lazy("email_already_verified_view")
            else:
                user.email_verified= True
                user.save()

                # log in the user and send him to the home page.
                login(self.request, user)
                return reverse_lazy("home_view")
        else:
            # this should not happen unless the link is manually tampered
            return reverse_lazy("email_verification_failed_view")

    def get_user(self):

        hmac_code = self.kwargs["hmac_code"]

        email = validate_code(hmac_code)

        if email is not None:
            try:
                user = StorybeepUser.objects.get(email = email)
                return user
            except StorybeepUser.DoesNotExist:
                return None


class EmailVerificationFailedView(TemplateView):
    """This view is shown when the verification link has been manually
    tampered
    """

    template_name = "email_verification_failed.html"


class PublisherSignupView(FormView):
    """Publishers are added to the system by adding a row in the
    VerifiedPublisher table, which automatically sends an email inviting
    the publisher to join. When the publisher clicks the link in this
    email, he is shown this view. It asks the publisher to set up
    a password. Upon entering the password, the publisher is logged in
    and redirected to the home page
    """

    template_name = "publisher_signup.html"
    form_class = PublisherSignupForm
    success_url = reverse_lazy("home_view")

    def get_context_data(self, *args, **kwargs):

        context = super(PublisherSignupView, self).get_context_data(
            *args, **kwargs)

        #this code needs to be used in the form's action attribute
        context["hmac_code"] = self.kwargs["hmac_code"]

        return context

    def get_publisher(self):
        """Checks if the link is valid and return the verified publisher
        object
        """

        hmac_code = self.kwargs["hmac_code"]
        email = validate_code(hmac_code)

        if email is None:
            #This should only happen if the verification link has been
            # manually tampered
            return redirect(reverse_lazy("email_verification_failed_view"))

        try:
            user = StorybeepUser.objects.get(email = email)
            #This happens if the link is being clicked the second time.
            return redirect(reverse_lazy("already_verified_view"))
        except StorybeepUser.DoesNotExist:
            pass

        try:
            #This check should always work out. I am being extra
            #defensive.
            publisher = VerifiedPublisher.objects.get(email = email)
            return publisher
        except VerifiedPublisher.DoesNotExist:
            return redirect(reverse_lazy("email_verification_failed_view"))

    def get(self, *args, **kwargs):

        publisher = self.get_publisher()
        set_language_in_session(publisher.language, self.request.session)

        return super(PublisherSignupView, self).get(*args, **kwargs)

    def form_valid(self, form):

        publisher = self.get_publisher()

        #Add the publisher as an user and log him in.
        user = form.save(publisher.email, publisher.language)
        login(self.request, user)

        return super(PublisherSignupView, self).form_valid(form)


class EmailAlreadyVerifiedView(TemplateView):
    """This is shown if the email is already verified"""

    template_name = "email_already_verified.html"


class SettingsView(LoginRequiredMixin, CommonContextMixin, FormView):

    form_class = SettingsForm
    template_name = "settings.html"
    success_url = reverse_lazy("home_view")

    def get_context_data(self, *args, **kwargs):

        context = super(SettingsView, self).get_context_data(
            *args, **kwargs)

        user = self.request.user
        if user.is_publisher:
            context["base_template"] = "publisher_base.html"
        else:
            context["base_template"] = "reader_base.html"

        return context

    def get_initial(self):

        language = self.request.user.settings.language
        return {"language" : language}

    def form_valid(self, form):

        settings = form.save(self.request.user)
        set_language_in_session(settings.language, self.request.session)

        return super(SettingsView, self).form_valid(form)
