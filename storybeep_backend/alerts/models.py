from django.db import models

class Alert(models.Model):

    story = models.ForeignKey("stories.Story")
    user = models.ForeignKey("users.StorybeepUser")
    time_added = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return "{0} is tracking {1}".format(self.user.email, self.story.title)

    class Meta:
        unique_together = (("story", "user"),)
