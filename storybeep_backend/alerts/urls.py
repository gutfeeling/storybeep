from django.conf.urls import url

from alerts.views import LandingView, StartTrackingView, StopTrackingView

urlpatterns = [
    url(
        regex  = r"^landing/$",
        view = LandingView.as_view(),
        name = "landing_view",
        ),
    url(
        regex  = r"^start-tracking/$",
        view = StartTrackingView.as_view(),
        name = "start_tracking_view",
        ),
    url(
        regex  = r"^stop-tracking/(?P<alert_id>.+)$",
        view = StopTrackingView.as_view(),
        name = "stop_tracking_view",
        ),
    ]
