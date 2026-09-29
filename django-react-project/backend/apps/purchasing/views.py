from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record
from apps.inventory.models import Product
from apps.purchasing.models import PurchaseOrder, PurchaseOrderLine, Supplier
from apps.purchasing.services import create_purchase_order, receive_goods
from core.api import required


def order_data(order):
    return {
        "id": order.id,
        "supplier_id": order.supplier_id,
        "supplier": order.supplier.name,
        "status": order.status,
        "expected_date": order.expected_date,
        "created_by": order.created_by.username,
        "lines": [
            {
                "product_id": line.product_id,
                "product": line.product.name,
                "quantity_ordered": line.quantity_ordered,
                "unit_cost": str(line.unit_cost),
                "quantity_received": line.quantity_received_so_far,
                "quantity_remaining": line.quantity_ordered - line.quantity_received_so_far,
            }
            for line in order.lines.all()
        ],
    }


class SupplierListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        suppliers = Supplier.objects.filter(is_active=True).order_by("name")
        return Response([
            {"id": item.id, "name": item.name, "phone": item.phone, "email": item.email, "address": item.address}
            for item in suppliers
        ])

    def post(self, request):
        error = required(request.data, "name")
        if error:
            return error
        name = str(request.data["name"]).strip()
        if not name:
            return Response({"detail": "Supplier name cannot be blank."}, status=400)
        supplier = Supplier.objects.create(
            name=name,
            phone=str(request.data.get("phone", "")).strip(),
            email=str(request.data.get("email", "")).strip(),
            address=str(request.data.get("address", "")).strip(),
        )
        record(request.user, "added", "Supplier", supplier.id, {"name": supplier.name})
        return Response(
            {"id": supplier.id, "name": supplier.name, "phone": supplier.phone, "email": supplier.email, "address": supplier.address},
            status=201,
        )


class PurchaseOrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = PurchaseOrder.objects.select_related("supplier", "created_by").prefetch_related("lines__product").order_by("-id")
        return Response([order_data(order) for order in orders])

    def post(self, request):
        error = required(request.data, "supplier", "lines")
        if error:
            return error
        lines = request.data["lines"]
        if not isinstance(lines, list) or not lines:
            return Response({"detail": "At least one product line is required."}, status=400)
        for line in lines:
            try:
                quantity = int(line.get("quantity_ordered", 0))
                unit_cost = float(line.get("unit_cost", 0))
            except (AttributeError, TypeError, ValueError):
                return Response({"detail": "Each line needs a valid product, positive quantity, and non-negative unit cost."}, status=400)
            if not line.get("product_id") or quantity <= 0 or unit_cost < 0:
                return Response({"detail": "Each line needs a valid product, positive quantity, and non-negative unit cost."}, status=400)
        try:
            product_ids = [line["product_id"] for line in lines]
            valid_product_ids = {str(pk) for pk in Product.objects.filter(pk__in=product_ids, is_archived=False).values_list("pk", flat=True)}
            if any(str(product_id) not in valid_product_ids for product_id in product_ids):
                return Response({"detail": "One or more purchase-order products do not exist or are archived."}, status=400)
            supplier = Supplier.objects.get(pk=request.data["supplier"], is_active=True)
            order = create_purchase_order(supplier, request.user, lines, request.data.get("expected_date") or None)
        except Supplier.DoesNotExist:
            return Response({"detail": "Supplier not found or inactive."}, status=404)
        except (PurchaseOrderLine.DoesNotExist, ValidationError, ValueError, TypeError):
            return Response({"detail": "Could not create the purchase order; check supplier and product IDs."}, status=400)
        order = PurchaseOrder.objects.select_related("supplier", "created_by").prefetch_related("lines__product").get(pk=order.pk)
        return Response(order_data(order), status=201)


class ReceiveGoodsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        error = required(request.data, "purchase_order_id", "lines")
        if error:
            return error
        lines = request.data["lines"]
        if not isinstance(lines, list) or not lines:
            return Response({"detail": "At least one received quantity is required."}, status=400)
        for line in lines:
            try:
                quantity = int(line.get("quantity_received", 0))
            except (AttributeError, TypeError, ValueError):
                return Response({"detail": "Each received line needs a product and a whole-number quantity."}, status=400)
            if not line.get("product_id") or quantity < 0:
                return Response({"detail": "Each received line needs a product and a non-negative quantity."}, status=400)
        try:
            order = receive_goods(
                request.data["purchase_order_id"],
                lines,
                request.user,
                request.data.get("delivery_note_ref", ""),
            )
        except PurchaseOrder.DoesNotExist:
            return Response({"detail": "Purchase order not found."}, status=404)
        except (PurchaseOrderLine.DoesNotExist, ValidationError, TypeError, ValueError):
            return Response({"detail": "Received quantities are invalid or exceed the order."}, status=400)
        order = PurchaseOrder.objects.select_related("supplier", "created_by").prefetch_related("lines__product").get(pk=order.pk)
        return Response(order_data(order))
