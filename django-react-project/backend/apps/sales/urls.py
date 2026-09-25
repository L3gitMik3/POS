from django.urls import path

from apps.sales.views import CustomerListCreateView, ReturnCreateView, SaleListCreateView, SaleVoidView, TillCloseView, TillCurrentView, TillOpenView

urlpatterns = [
    path("", SaleListCreateView.as_view()),
    path("customers/", CustomerListCreateView.as_view()),
    path("till/open/", TillOpenView.as_view()),
    path("till/current/", TillCurrentView.as_view()),
    path("till/close/", TillCloseView.as_view()),
    path("tills/open/", TillOpenView.as_view()),
    path("tills/current/", TillCurrentView.as_view()),
    path("tills/close/", TillCloseView.as_view()),
    path("returns/", ReturnCreateView.as_view()),
    path("<uuid:sale_id>/void/", SaleVoidView.as_view()),
]