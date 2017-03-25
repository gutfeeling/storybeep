from django.views.generic import TemplateView
from django.views import View
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.http import Http404
from django.http import HttpResponse

from storybeep_backend.views import CommonContextMixin
from users.views import ReaderOnlyAccessMixin
from users.models import StorybeepUser
from stories.models import Article, Story
from alerts.models import Alert, ReadingData
from utils.sign import validate_code


class LandingView(CommonContextMixin, TemplateView):

    template_name = "landing.html"

    def get_context_data(self, *args, **kwargs):

        context = super(LandingView, self).get_context_data(*args, **kwargs)

        context["story_title"] = self.story.title
        context["story_id"] = self.story.id

        user = self.request.user

        if user.is_authenticated:
            #Use different templates for logged in users
            if user.is_publisher:
                context["base_template"] = "publisher_base.html"
            else:
                context["base_template"] = "reader_base.html"

        else:
            context["base_template"] = "base.html"

        return context


    def get(self, *args, **kwargs):

        article_url = self.request.GET.get("url", None)

        try:
            self.article = Article.objects.get(url = article_url)
        except Article.DoesNotExist:
            #Happens when te url does not correspond to an article
            #added by a publisher in Storybeep.
            raise Http404

        self.story = self.article.story

        #Set a session parameter so that we can automatically add the story
        #to the users tracked list when he signs up or logs in.
        self.request.session["wants_to_track"] = self.story.id

        return super(LandingView, self).get(*args, **kwargs)


class StartTrackingView(View):
    """This view handles what happens when someone clicks on the track
    story button. If the user is logged in, the story is added to their
    tracking list and the user is redirected to the home page. If the
    user is not logged in, he is redirected to the signup page
    """

    def get(self, *args, **kwargs):

        story_id = self.request.GET.get("story", None)

        try:
            #This would only happen if the session parameter is manually
            #tampered.
            self.story = Story.objects.get(id = story_id)
        except Story.DoesNotExist:
            raise Http404


        #Set a session parameter so that we can automatically add the story
        #to the users tracked list when he signs up or logs in.
        self.request.session["wants_to_track"] = story_id

        user = self.request.user

        if user.is_authenticated:
            if user.is_publisher:
                #Publishers are not allowed to track stories.
                #Need helpful error messages!
                raise Http404
            else:
                return redirect(reverse_lazy("home_view"))
        else:
            return redirect(reverse_lazy("signup_view"))


class StopTrackingView(ReaderOnlyAccessMixin, View):
    """Stop tracking a story"""

    def get_alert_id(self):
        alert_id = self.kwargs.get("alert_id", None)
        try:
            alert_id = int(alert_id)
            return alert_id
        except ValueError:
            raise Http404

    def test_func(self, *args, **kwargs):
        """Assures that only the correct user can perform this
        destructive action
        """

        can_access = super(StopTrackingView, self).test_func(*args, **kwargs)
        if can_access:
            alert_id = self.get_alert_id()
            try:
                alert = Alert.objects.get(id = alert_id)
                if self.request.user == alert.user:
                    can_access = True
                else:
                    #Happens if one user tries to delete another users
                    #another user's alert.
                    self.raise_exception = True
                    can_access = False
            except Alert.DoesNotExist:
                pass

        return can_access

    def get(self, *args, **kwargs):

        alert_id = self.get_alert_id()

        try:
            this_alert = Alert.objects.get(id = alert_id)
            this_alert.delete()
            return HttpResponse("")
        except Alert.DoesNotExist:
            raise Http404


class ReadView(View):

    def get_user(self):

        hmac_code = self.request.GET.get("hmac_code", None)

        if hmac_code is None:

            # reading directly from website
            if self.request.user.is_authenticated:
                return self.request.user
            else:
                # users who are not logged in should not get access to
                # these links. so this situation should not arise
                # unless someone directly writes the url on the
                # address bar.
                return None

        # reading from email

        email = validate_code(hmac_code, None)

        if email is not None:
            try:
                user = StorybeepUser.objects.get(email = email)
                return user
            except StorybeepUser.DoesNotExist:
                return None

    def get_article(self):

        url = self.request.GET.get("url", None)

        try:
            article = Article.objects.get(url = url)
            return article
        except Article.DoesNotExist:
            return None

    def get(self, *args, **kwargs):

        article = self.get_article()
        user = self.get_user()

        if article is None or user is None:
            raise Http404

        try:
            reading_data = ReadingData.objects.get(
                user = user, article = article
                )
            reading_data.count += 1
            reading_data.save()
        except ReadingData.DoesNotExist:
            new_reading_data = ReadingData(
                user = user, article = article, count = 1
                )
            new_reading_data.save()

        return redirect(article.url)
