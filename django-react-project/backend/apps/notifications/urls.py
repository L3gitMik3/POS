from django.urls import path

from apps.notifications.views import NotificationListCreateView, NotificationReadView

urlpatterns = [
    path("", NotificationListCreateView.as_view()),
    path("read/", NotificationReadView.as_view()),
]
