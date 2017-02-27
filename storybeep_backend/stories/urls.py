from django.conf.urls import url

from stories.views import AddArticleView, StoryDetailView, StoryListView

urlpatterns = [
    url(
        regex  = r"^add-article/$",
        view = AddArticleView.as_view(),
        name = "add_article_view",
        ),
    url(
        regex  = r"^stories/$",
        view = StoryListView.as_view(),
        name = "story_list_view",
        ),
    url(
        regex  = r"^story/(?P<story_id>\d+)$",
        view = StoryDetailView.as_view(),
        name = "story_detail_view",
        ),
    ]
