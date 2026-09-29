from django.db import models

from core.models import TenantBaseModel, TenantScopedModel


class Category(TenantScopedModel):
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Product(TenantBaseModel):
    sku = models.CharField(max_length=100)
    barcode = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    unit = models.CharField(max_length=20, default="piece")
    low_stock_threshold = models.IntegerField(default=0)
    is_archived = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tenant_schema", "sku"], name="uniq_product_sku_per_tenant"),
            models.UniqueConstraint(fields=["tenant_schema", "barcode"], name="uniq_product_barcode_per_tenant"),
        ]

    @property
    def tax_amount(self):
        return self.sale_price * self.tax_rate / (100 + self.tax_rate)

    def __str__(self):
        return self.name


class StockMovement(TenantScopedModel):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stock_movements")
    quantity_delta = models.IntegerField()
    reason = models.CharField(max_length=64)
    reference_id = models.UUIDField(null=True, blank=True)
    created_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["product", "id"]),
            models.Index(fields=["reason", "created_at"]),
        ]
