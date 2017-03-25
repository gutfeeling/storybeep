from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils.translation import LANGUAGE_SESSION_KEY

from stories.models import Story
from alerts.models import Alert


class CommonContextMixin(object):
    """This mixin makes the email of the logged in user available as
    a template tag. It is responsible for the email to appear in the
    rightmost part of the navbar
    """

    def get_context_data(self, **kwargs):

        context = super(CommonContextMixin, self).get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            user = self.request.user
            context["email"] = user.email

        return context


class SessionMixin(object):

    def track_stories_from_session_data(self, user):
        story_id = self.request.session.get("wants_to_track", None)

        if story_id is not None:
            try:
                story = Story.objects.get(id = story_id)
                try:
                    Alert.objects.get(story = story, user = user)
                    # inform the user that he is already subscribed
                    # to this story
                except Alert.DoesNotExist:
                    new_alert = Alert(story = story, user = user)
                    new_alert.save()
            except Story.DoesNotExist:
                pass
            self.request.session["wants_to_track"] = None


class HomeView(CommonContextMixin, SessionMixin, TemplateView):

    template_name = "home.html"

    def get_context_data(self, **kwargs):

        context = super(HomeView, self).get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            user = self.request.user
            if user.is_publisher:
                self.template_name = "publisher_home.html"
            else:
                self.template_name = "reader_home.html"

                #If the reader logs in after visiting a landing page, then
                #this line ensures that he automatically starts tracking the
                #story upon login.
                self.track_stories_from_session_data(user)

                alerts = Alert.objects.filter(user = user)
                alerts_sorted_by_unread = sorted(
                    alerts, key = lambda item: -item.unread_count()
                    )

                context["object_list"] = alerts_sorted_by_unread

        return context


class ChangeLanguageView(RedirectView):

    def get_redirect_url(self):
        language = self.request.GET.get("language", None)
        redirect_url = self.request.GET.get("next", None)

        if language is not None:
            self.request.session[LANGUAGE_SESSION_KEY] = language

        if redirect_url is None:
            redirect_url = "/"

        return redirect_url
