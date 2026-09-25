from django.urls import path

from apps.payments.views import MpesaCallbackView, MpesaInitiateView

urlpatterns = [
    path("mpesa/initiate/", MpesaInitiateView.as_view()),
    path("mpesa/callback/", MpesaCallbackView.as_view()),
]