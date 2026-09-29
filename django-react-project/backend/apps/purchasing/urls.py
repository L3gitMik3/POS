from django.urls import path

from apps.purchasing.views import PurchaseOrderListCreateView, ReceiveGoodsView, SupplierListCreateView

urlpatterns = [
    path("suppliers/", SupplierListCreateView.as_view()),
    path("orders/", PurchaseOrderListCreateView.as_view()),
    path("receive/", ReceiveGoodsView.as_view()),
]
