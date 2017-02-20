from django.conf.urls import url

from alerts.views import SubscribeView

urlpatterns = [
    url(
        regex  = r"^$",
        view = SubscribeView.as_view(),
        name = "subscribe_view",
        ),
]
