from django.urls import path

from apps.inventory.views import ProductDetailView, ProductListCreateView, StockAdjustView
from apps.inventory.category_views import CategoryListCreateView

urlpatterns = [
    path("products/", ProductListCreateView.as_view()),
    path("products/<uuid:pk>/", ProductDetailView.as_view()),
    path("categories/", CategoryListCreateView.as_view()),
    path("stock/adjust/", StockAdjustView.as_view()),
]