from django import forms

import requests
from bs4 import BeautifulSoup

from stories.models import Article, Story

class AddArticleForm(forms.Form):

    #Need to add autocomplete to this form

    url = forms.URLField(
        widget = forms.TextInput(
            attrs = {"placeholder" : "URL of the article"}
            )
        )
    story_title = forms.CharField(
        widget = forms.TextInput(
            attrs = {"placeholder" : "Story"}
            )
        )

    def save_and_return_story_id(self, user):

        url = self.cleaned_data["url"]
        story_title = self.cleaned_data["story_title"]

        try:
            story = Story.objects.get(title = story_title, created_by = user)
            article = Article(url = url, story = story, created_by = user)
        except Story.DoesNotExist:
            story = Story(title = story_title, created_by = user)
            story.save()
            article = Article(url = url, story = story, created_by = user)

        #Get title and picture using the Open Graph meta tags in the html
        #file of the article

        response = requests.get(article.url)
        html_soup = BeautifulSoup(response.text, "html.parser")

        title = html_soup.find("meta", property = "og:title")["content"]
        image_url = html_soup.find("meta", property = "og:image")["content"]

        article.title = title
        article.image_url = image_url

        article.save()

        return story.id
