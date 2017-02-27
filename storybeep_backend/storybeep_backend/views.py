from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin

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
                self.template_name = "publisher-home.html"
            else:
                self.template_name = "reader-home.html"

                #If the reader logs in after visiting a landing page, then
                #this line ensures that he automatically starts tracking the
                #story upon login.
                self.track_stories_from_session_data(user)

                context["object_list"] = Alert.objects.filter(user = user)

        return context
