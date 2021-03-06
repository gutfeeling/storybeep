from django.db import models
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.utils import translation
from django.urls import reverse_lazy
import django_rq

from alerts.models import Alert
from utils.sign import get_hmac_code

class Article(models.Model):

    url = models.URLField(unique = True, max_length = 500)
    time_added = models.DateTimeField(auto_now_add = True)
    story = models.ForeignKey("Story")
    title = models.TextField(null = True, blank = True)
    image_url = models.URLField(null = True, blank = True, max_length = 500)
    created_by = models.ForeignKey("users.StorybeepUser")

    def send_notifications(self):

        try:
            mailer = settings.MAILER
        except AttributeError:
            raise ImproperlyConfigured("Please set the MAILER settings.")

        current_site = Site.objects.get_current()
        domain = current_site.domain

        # change http to https at some point
        # use reverse? reverse uses relative urls, can be make it work?
        storybeep_logo_url = ("http://{0}/static/images/"
            "storybeep_logo.png".format(domain))

        alert_list = Alert.objects.filter(story = self.story)

        for alert in alert_list:
            recipient_email = alert.user.email
            recipient_language =  alert.user.settings.language
            unsubscribe_url = "http://{0}/stop-tracking/{1}/".format(domain,
                alert.id)

            hmac_code = get_hmac_code(recipient_email)
            article_url = "http://{0}/read?url={1}&hmac_code={2}".format(
                domain, self.url, hmac_code,
                )

            with translation.override(recipient_language):

                text_message = render_to_string("email_notification.txt",
                    {"story_title" : self.story.title,
                     "article_url" : article_url,
                     }
                    )

                html_message = render_to_string("email_notification.html",
                    {"story_title" : self.story.title,
                     "storybeep_logo_url" : storybeep_logo_url,
                     "article_title" : self.title,
                     "article_url" : article_url,
                     "article_picture_url" : self.image_url,
                     "unsubscribe_url" : unsubscribe_url,
                     }
                    )

            send_mail(
                subject = "News on {0}".format(self.story.title),
                message = text_message,
                html_message = html_message,
                from_email = "Storybeep <{0}>".format(mailer),
                recipient_list = [recipient_email,],
                fail_silently = False,
                )


    def save(self, *args, **kwargs):
        django_rq.enqueue(self.send_notifications)
        super(Article, self).save(*args, *kwargs)


    def __str__(self):
        return self.url

class Story(models.Model):

    title = models.CharField(max_length = 200)
    time_added = models.DateTimeField(auto_now_add = True)
    created_by = models.ForeignKey("users.StorybeepUser")

    def latest_article(self):
        return self.article_set.all().order_by("-time_added")[0]

    def __str__(self):
        return self.title
