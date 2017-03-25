from django.db import models

class Alert(models.Model):

    story = models.ForeignKey("stories.Story")
    user = models.ForeignKey("users.StorybeepUser")
    time_added = models.DateTimeField(auto_now_add = True)

    def unread_count(self):
        article_count = self.story.article_set.all().count()
        read_count = ReadingData.objects.filter(
            article__story = self.story, user = self.user
            ).count()
        unread_count = article_count - read_count

        return unread_count

    def publisher_name(self):
        return self.story.created_by.settings.name


    def __str__(self):
        return "{0} is tracking {1}".format(self.user.email, self.story.title)

    class Meta:
        unique_together = (("story", "user"),)


class ReadingData(models.Model):

    user = models.ForeignKey("users.StorybeepUser")
    article = models.ForeignKey("stories.Article")
    first_read_at = models.DateTimeField(auto_now_add = True)
    count = models.IntegerField()

    def __str__(self):
        return "{0} was read by {1} {2} times, first on {3}".format(
            self.article.url, self.user.email, self.count, self.first_read_at
            )

    class Meta:
        unique_together = (("user", "article"),)
