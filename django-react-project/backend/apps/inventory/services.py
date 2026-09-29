from __future__ import annotations

from decimal import Decimal

from datetime import timedelta

from django.db import transaction
from django.db.models import F, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.audit.services import record
from apps.inventory.models import Product, StockMovement
from apps.notifications.services import notify_low_stock

STOCK_ADJUSTMENT_REASONS = {
    "restock",
    "sale",
    "damage",
    "expiry",
    "theft",
    "correction",
    "customer_return",
    "transfer",
    "other",
}


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


@transaction.atomic
def record_movement(product_id, delta, reason, reference_id, actor):
    product = Product.objects.select_for_update().get(pk=product_id)
    movement = StockMovement.objects.create(
        product_id=product_id,
        quantity_delta=delta,
        reason=reason,
        reference_id=reference_id,
        created_by=actor,
    )
    stock = get_current_stock(product_id)
    notify_low_stock(product, stock)
    return movement


def deduct_sale_stock(sale_id, cart_lines, actor):
    """Deduct each sold quantity once, using the sale as the idempotency key."""
    product_ids = [str(line["product_id"]) for line in cart_lines]
    requested = {}
    for line in cart_lines:
        product_id = str(line["product_id"])
        product_key = str(product_id)
        quantity = int(line["quantity"])
        if quantity <= 0:
            raise ValueError("Sale quantities must be greater than zero.")
        requested[product_key] = requested.get(product_key, 0) + quantity

    with transaction.atomic():
        locked_products = lock_products(product_ids)
        if len(locked_products) != len(set(product_ids)):
            raise ValueError("One or more products no longer exist.")
        if StockMovement.objects.filter(reference_id=sale_id, reason="sale").exists():
            return

        stock_map = {str(product_id): quantity for product_id, quantity in get_stock_map(product_ids).items()}
        insufficient = [
            product_id
            for product_id, quantity in requested.items()
            if stock_map.get(product_id, 0) < quantity
        ]
        if insufficient:
            raise ValueError(f"Insufficient stock for product(s): {', '.join(insufficient)}")

        for product_id, quantity in requested.items():
            record_movement(product_id, -quantity, "sale", sale_id, actor)


def reverse_movements(reference_id, reason, actor):
    movements = StockMovement.objects.filter(reference_id=reference_id, reason="sale")
    for movement in movements:
        record_movement(
            product_id=movement.product_id,
            delta=-movement.quantity_delta,
            reason=reason,
            reference_id=reference_id,
            actor=actor,
        )
    return movements.count()


def adjust_stock(product_id, counted_quantity, reason, note, actor):
    counted_quantity = int(counted_quantity)
    if counted_quantity < 0:
        raise ValueError("Counted stock cannot be negative.")
    if reason not in STOCK_ADJUSTMENT_REASONS:
        raise ValueError("Choose a valid stock adjustment reason.")
    if reason == "other" and not str(note).strip():
        raise ValueError("Add a note when the reason is Other.")
    with transaction.atomic():
        product = Product.objects.select_for_update().get(pk=product_id)
        current = get_current_stock(product_id)
        delta = counted_quantity - current
        if delta == 0:
            return product
        record_movement(product_id, delta, f"adjustment_{reason}", None, actor)
        record(
            actor,
            "stock_added" if delta > 0 else "stock_removed",
            "Product",
            str(product_id),
            {
                "reason": reason,
                "note": str(note).strip(),
                "previous_quantity": current,
                "counted_quantity": counted_quantity,
                "delta": delta,
            },
            ip=None,
        )
        return product


def low_stock_products():
    return (
        Product.objects.filter(is_archived=False, low_stock_threshold__gt=0)
        .annotate(stock_on_hand=Coalesce(Sum("stock_movements__quantity_delta"), Value(0)))
        .filter(stock_on_hand__lte=F("low_stock_threshold"))
    )


def dead_stock_products(days):
    cutoff = timezone.now() - timedelta(days=days)
    last_movement = StockMovement.objects.filter(product_id=OuterRef("pk")).order_by("-created_at").values("created_at")[:1]
    return (
        Product.objects.filter(is_archived=False)
        .annotate(
            stock_on_hand=Coalesce(Sum("stock_movements__quantity_delta"), Value(0)),
            last_movement_at=Subquery(last_movement),
        )
        .filter(stock_on_hand__gt=0)
        .filter(Q(last_movement_at__lt=cutoff) | Q(last_movement_at__isnull=True))
    ).distinct()
