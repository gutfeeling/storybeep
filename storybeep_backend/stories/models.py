from django.db import models

class Article(models.Model):

    url = models.URLField(unique = True, max_length = 500)
    time_added = models.DateTimeField(auto_now_add = True)
    story = models.ForeignKey("Story")
    title = models.TextField(null = True, blank = True)
    image_url = models.URLField(null = True, blank = True, max_length = 500)
    created_by = models.ForeignKey("users.StorybeepUser")

    def __str__(self):
        return self.url

class Story(models.Model):

    title = models.CharField(max_length = 200)
    time_added = models.DateTimeField(auto_now_add = True)
    created_by = models.ForeignKey("users.StorybeepUser")

    def __str__(self):
        return self.title
