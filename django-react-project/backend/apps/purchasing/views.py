from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.purchasing.models import PurchaseOrder
from apps.purchasing.services import create_purchase_order, receive_goods
from core.api import required


def order_data(order):
    return {"id": order.id, "supplier": order.supplier_id, "status": order.status, "expected_date": order.expected_date, "created_by": str(order.created_by_id), "lines": [{"product_id": line.product_id, "quantity_ordered": line.quantity_ordered, "unit_cost": str(line.unit_cost), "quantity_received": line.quantity_received_so_far} for line in order.lines.all()]}


class PurchaseOrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([order_data(order) for order in PurchaseOrder.objects.prefetch_related("lines").order_by("-id")])

    def post(self, request):
        error = required(request.data, "supplier", "lines")
        if error:
            return error
        order = create_purchase_order(request.data["supplier"], request.user, request.data["lines"])
        return Response(order_data(order), status=201)


class ReceiveGoodsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        error = required(request.data, "purchase_order_id", "lines")
        if error:
            return error
        order = receive_goods(request.data["purchase_order_id"], request.data["lines"], request.user)
        return Response(order_data(order))
