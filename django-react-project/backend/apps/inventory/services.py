from __future__ import annotations

from decimal import Decimal

from datetime import timedelta

from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone

from apps.audit.services import record
from apps.inventory.models import Product, StockMovement


def get_current_stock(product_id):
    return (
        StockMovement.objects.filter(product_id=product_id).aggregate(total=Sum("quantity_delta"))["total"]
        or 0
    )


def get_stock_map(product_ids):
    rows = StockMovement.objects.filter(product_id__in=product_ids).values("product_id").annotate(total=Sum("quantity_delta"))
    return {row["product_id"]: row["total"] or 0 for row in rows}


def lock_products(product_ids):
    ids = sorted(set(product_ids))
    products = list(Product.objects.select_for_update().filter(id__in=ids))
    return {product.id: product for product in products}


def record_movement(product_id, delta, reason, reference_id, actor):
    return StockMovement.objects.create(
        product_id=product_id,
        quantity_delta=delta,
        reason=reason,
        reference_id=reference_id,
        created_by=actor,
    )


def deduct_sale_stock(sale_id, cart_lines, actor):
    """Deduct each sold quantity once, using the sale as the idempotency key."""
    if StockMovement.objects.filter(reference_id=sale_id, reason="sale").exists():
        return

    product_ids = [line["product_id"] for line in cart_lines]
    stock_map = {str(product_id): quantity for product_id, quantity in get_stock_map(product_ids).items()}
    requested = {}
    for line in cart_lines:
        product_id = line["product_id"]
        product_key = str(product_id)
        requested[product_key] = requested.get(product_key, 0) + int(line["quantity"])
    insufficient = [
        str(product_id)
        for product_id, quantity in requested.items()
        if stock_map.get(product_id, 0) < quantity
    ]
    if insufficient:
        raise ValueError(f"Insufficient stock for product(s): {', '.join(insufficient)}")

    for product_id, quantity in requested.items():
        record_movement(product_id, -quantity, "sale", sale_id, actor)


def reverse_movements(reference_id, reason, actor):
    movements = StockMovement.objects.filter(reference_id=reference_id)
    for movement in movements:
        record_movement(
            product_id=movement.product_id,
            delta=-movement.quantity_delta,
            reason=reason,
            reference_id=reference_id,
            actor=actor,
        )
    return movements.count()


def adjust_stock(product_id, counted_quantity, note, actor):
    product = Product.objects.get(pk=product_id)
    current = get_current_stock(product_id)
    delta = counted_quantity - current
    if delta == 0:
        return product

    with transaction.atomic():
        record_movement(product_id, delta, "adjustment", None, actor)
        record(actor, "adjust_stock", "Product", str(product_id), {"note": note, "delta": delta}, ip=None)
    return product


def low_stock_products():
    return Product.objects.filter(is_archived=False, low_stock_threshold__gt=0).filter(
        stock__lt=F("low_stock_threshold")
    )


def dead_stock_products(days):
    cutoff = timezone.now() - timedelta(days=days)
    return Product.objects.filter(is_archived=False).filter(
        stock_movements__created_at__lt=cutoff
    ).distinct()
