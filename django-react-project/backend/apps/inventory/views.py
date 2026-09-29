from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inventory.models import Category, Product
from apps.inventory.services import STOCK_ADJUSTMENT_REASONS, adjust_stock, get_current_stock
from apps.audit.services import record
from core.api import required


def product_data(product):
    return {"id": str(product.id), "sku": product.sku, "barcode": product.barcode, "name": product.name, "category": product.category_id, "cost_price": str(product.cost_price), "sale_price": str(product.sale_price), "tax_rate": str(product.tax_rate), "unit": product.unit, "low_stock_threshold": product.low_stock_threshold, "is_archived": product.is_archived, "stock": get_current_stock(product.id)}


def client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    return forwarded_for.split(",", 1)[0].strip() if forwarded_for else request.META.get("REMOTE_ADDR")


class ProductListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([product_data(product) for product in Product.objects.select_related("category").filter(is_archived=False)])

    def post(self, request):
        error = required(request.data, "sku", "name", "category")
        if error:
            return error
        if not Category.objects.filter(pk=request.data["category"], is_active=True).exists():
            return Response({"detail": "Category not found or inactive in this store."}, status=400)
        product = Product.objects.create(
            sku=request.data["sku"], barcode=request.data.get("barcode"), name=request.data["name"], category_id=request.data["category"],
            cost_price=request.data.get("cost_price", 0), sale_price=request.data.get("sale_price", request.data.get("price", 0)),
            tax_rate=request.data.get("tax_rate", 0), unit=request.data.get("unit", "piece"),
            low_stock_threshold=request.data.get("low_stock_threshold", request.data.get("reorder_level", 0)),
        )
        opening_stock = int(request.data.get("stock_quantity", 0) or 0)
        if opening_stock:
            from apps.inventory.services import record_movement

            record_movement(product.id, opening_stock, "opening_stock", None, request.user)
        record(request.user, "added", "Product", product.id, {"name": product.name, "sku": product.sku, "opening_stock": opening_stock}, client_ip(request))
        return Response(product_data(product), status=201)


class ProductDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return Product.objects.get(pk=pk)

    def patch(self, request, pk):
        try:
            product = self.get_object(pk)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        fields = {
            "name": "name",
            "sku": "sku",
            "barcode": "barcode",
            "category": "category_id",
            "cost_price": "cost_price",
            "price": "sale_price",
            "sale_price": "sale_price",
            "tax_rate": "tax_rate",
            "unit": "unit",
            "reorder_level": "low_stock_threshold",
            "low_stock_threshold": "low_stock_threshold",
        }
        changed = []
        for incoming, model_field in fields.items():
            if incoming in request.data:
                if incoming == "category" and not Category.objects.filter(pk=request.data[incoming], is_active=True).exists():
                    return Response({"detail": "Category not found or inactive in this store."}, status=400)
                setattr(product, model_field, request.data[incoming])
                changed.append(model_field)

        if "is_active" in request.data:
            product.is_archived = not bool(request.data["is_active"])
            changed.append("is_archived")

        if changed:
            change_reason = str(request.data.get("change_reason", "")).strip()
            if change_reason not in {"routine_update", "pricing_update", "barcode_correction", "data_correction", "other"}:
                return Response({"detail": "Choose a reason for editing this product."}, status=400)
            change_note = str(request.data.get("change_note", "")).strip()
            if change_reason == "other" and not change_note:
                return Response({"detail": "Explain the change when the reason is Other."}, status=400)
            product.save(update_fields=sorted(set(changed + ["updated_at"])))
            record(
                request.user,
                "updated",
                "Product",
                product.id,
                {
                    "reason": change_reason,
                    "note": change_note,
                    "fields": {field: str(getattr(product, field)) for field in sorted(set(changed))},
                },
                client_ip(request),
            )

        stock_key = next((key for key in ("stock_quantity", "stock", "quantity_on_hand") if key in request.data), None)
        if stock_key:
            try:
                product = adjust_stock(
                    product.id,
                    request.data[stock_key],
                    request.data.get("stock_reason", "correction"),
                    request.data.get("stock_note", request.data.get("note", "Product stock update")),
                    request.user,
                )
            except (TypeError, ValueError):
                return Response({"detail": "Stock quantity or stock reason is invalid."}, status=400)
        return Response(product_data(product))

    def delete(self, request, pk):
        reason = str(request.data.get("reason", "")).strip()
        if reason not in {"discontinued", "duplicate", "incorrect_item", "other"}:
            return Response({"detail": "Choose a reason before archiving this product."}, status=400)
        note = str(request.data.get("note", "")).strip()
        if reason == "other" and not note:
            return Response({"detail": "Explain why the product is being archived."}, status=400)
        try:
            product = self.get_object(pk)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        product.is_archived = True
        product.save(update_fields=["is_archived", "updated_at"])
        record(
            request.user,
            "deleted",
            "Product",
            product.id,
            {"name": product.name, "sku": product.sku, "reason": reason, "note": note, "deletion_type": "archived"},
            client_ip(request),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class StockAdjustView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        error = required(request.data, "product_id", "counted_quantity", "reason")
        if error:
            return error
        if request.data["reason"] not in STOCK_ADJUSTMENT_REASONS:
            return Response({"detail": "Choose a valid reason for this stock change."}, status=400)
        try:
            product = adjust_stock(
                request.data["product_id"],
                request.data["counted_quantity"],
                request.data["reason"],
                request.data.get("note", ""),
                request.user,
            )
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=404)
        except (TypeError, ValueError, ValidationError):
            return Response({"detail": "Counted stock must be a non-negative whole number."}, status=400)
        return Response(product_data(product))