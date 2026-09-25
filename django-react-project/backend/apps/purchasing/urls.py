from django.urls import path

from apps.purchasing.views import PurchaseOrderListCreateView, ReceiveGoodsView

urlpatterns = [
    path("orders/", PurchaseOrderListCreateView.as_view()),
    path("receive/", ReceiveGoodsView.as_view()),
]
