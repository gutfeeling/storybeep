from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView
from django.shortcuts import get_object_or_404

from storybeep_backend.views import CommonContextMixin
from users.views import PublisherOnlyAccessMixin
from stories.forms import AddArticleForm
from stories.models import Story, Article


class CreatorOnlyAccessMixin(PublisherOnlyAccessMixin):
    """Ensures that only the creator of a resource has access. Any
    class inheriting this should define a get_creator() method which
    returns the creator of the resource
    """

    def test_func(self):
        can_access = super(CreatorOnlyAccessMixin, self).test_func()
        if can_access:
            creator = self.get_creator()
            if self.request.user == creator:
                return True
            else:
                self.raise_exception = True


class AddArticleView(PublisherOnlyAccessMixin, CommonContextMixin, FormView):
    """Add an article. Redirects to the story page of the story
    corresponding to the article.
    """

    template_name = "add_article.html"
    form_class = AddArticleForm

    def form_valid(self, form):

        user = self.request.user
        story_id = form.save_and_return_story_id(user)
        self.success_url = reverse_lazy(
            "story_detail_view",
            kwargs = {"story_id" : story_id},
            )
        return super(AddArticleView, self).form_valid(form)


class StoryListView(PublisherOnlyAccessMixin, CommonContextMixin, ListView):

    model = Story
    template_name = "stories.html"

    def get_queryset(self, **kwargs):
        queryset = super(StoryListView, self).get_queryset(**kwargs)
        user = self.request.user

        return queryset.filter(created_by = user)


class StoryDetailView(CreatorOnlyAccessMixin, CommonContextMixin, ListView):

    model = Article
    template_name = "story_detail.html"

    def get_creator(self):
        story_id = self.kwargs["story_id"]
        self.story = get_object_or_404(Story, id = story_id)

        return self.story.created_by

    def get_queryset(self, **kwargs):
        queryset = super(StoryDetailView, self).get_queryset(**kwargs)
        return queryset.filter(story = self.story)

    def get_context_data(self, **kwargs):
        context = super(StoryDetailView, self).get_context_data(**kwargs)
        context["story"] = self.story
        return context
