from django.db import models
from django.core.mail import send_mail
from django.conf import settings
import django_rq

from alerts.models import Alert

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

        recipients = Alert.objects.filter(story = self.story).values_list(
            "user__email", flat = True,
            ).order_by("id")

        send_mail(
            subject = "New article in {0}".format(self.story.title),
            message = self.url,
            from_email = mailer,
            recipient_list = recipients,
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

    def __str__(self):
        return self.title
