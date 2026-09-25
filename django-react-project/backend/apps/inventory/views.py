from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inventory.models import Category, Product
from apps.inventory.services import adjust_stock, get_current_stock
from core.api import required


def product_data(product):
    return {"id": str(product.id), "sku": product.sku, "barcode": product.barcode, "name": product.name, "category": product.category_id, "cost_price": str(product.cost_price), "sale_price": str(product.sale_price), "tax_rate": str(product.tax_rate), "unit": product.unit, "low_stock_threshold": product.low_stock_threshold, "is_archived": product.is_archived, "stock": get_current_stock(product.id)}


class ProductListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([product_data(product) for product in Product.objects.select_related("category").filter(is_archived=False)])

    def post(self, request):
        error = required(request.data, "sku", "name", "category")
        if error:
            return error
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
                setattr(product, model_field, request.data[incoming])
                changed.append(model_field)

        if "is_active" in request.data:
            product.is_archived = not bool(request.data["is_active"])
            changed.append("is_archived")

        if changed:
            product.save(update_fields=sorted(set(changed + ["updated_at"])))

        if "stock_quantity" in request.data:
            from apps.inventory.services import adjust_stock

            product = adjust_stock(product.id, int(request.data["stock_quantity"]), "Product stock update", request.user)
        return Response(product_data(product))

    def delete(self, request, pk):
        try:
            product = self.get_object(pk)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        product.is_archived = True
        product.save(update_fields=["is_archived", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class StockAdjustView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        error = required(request.data, "product_id", "counted_quantity")
        if error:
            return error
        product = adjust_stock(request.data["product_id"], int(request.data["counted_quantity"]), request.data.get("note", ""), request.user)
        return Response(product_data(product))