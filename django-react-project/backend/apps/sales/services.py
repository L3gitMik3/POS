from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.inventory.services import deduct_sale_stock
from apps.sales.models import Sale, SaleLine, TillSession


def compute_totals(cart_lines, discount):
    subtotal = sum((Decimal(str(line["quantity"])) * Decimal(str(line["unit_price"]))) for line in cart_lines)
    discount_value = Decimal(str(discount or 0))
    tax_total = sum((Decimal(str(line["quantity"])) * Decimal(str(line["unit_price"])) * Decimal(str(line.get("tax_rate", 0))) / Decimal("100")) for line in cart_lines)
    total = subtotal - discount_value + tax_total
    return {"subtotal": subtotal, "discount_amount": discount_value, "tax_amount": tax_total, "total_amount": total}


def create_sale(cart_lines, cashier, till_session, payment_method, customer=None, discount=None, override_token=None):
    with transaction.atomic():
        totals = compute_totals(cart_lines, discount)
        sale = Sale.objects.create(
            receipt_number=f"INV-{cashier.pk}-{Sale.objects.count() + 1:05d}",
            till_session=till_session,
            cashier=cashier,
            customer=customer,
            payment_method=payment_method,
            subtotal=totals["subtotal"],
            discount_amount=totals["discount_amount"],
            tax_amount=totals["tax_amount"],
            total_amount=totals["total_amount"],
            payment_status="paid" if payment_method == "cash" else "pending",
        )

        for line in cart_lines:
            SaleLine.objects.create(
                sale=sale,
                product_id=line["product_id"],
                quantity=line["quantity"],
                unit_price=line["unit_price"],
                tax_rate=line.get("tax_rate", 0),
                line_total=Decimal(str(line["quantity"])) * Decimal(str(line["unit_price"])),
            )

        if payment_method == "cash":
            deduct_sale_stock(sale.id, cart_lines, cashier)
    return sale


def void_sale(sale_id, actor, override_token):
    sale = Sale.objects.get(id=sale_id)
    if sale.status == "voided":
        raise ValueError("Sale already voided")
    sale.status = "voided"
    sale.payment_status = "failed"
    sale.save(update_fields=["status", "payment_status", "updated_at"])
    return sale


def process_return(*args, **kwargs):
    return {"ok": True}


def open_till(user, terminal_id, float_amount):
    session = TillSession.objects.filter(terminal_id=terminal_id).first()
    if session and not session.closed_at:
        raise ValueError("Till already open")
    return TillSession.objects.create(
        terminal_id=terminal_id,
        opened_by=user,
        opening_float=float_amount,
    )


def close_till(session, counted_cash):
    session.counted_cash = counted_cash
    session.expected_cash = session.opening_float
    session.variance = Decimal(str(counted_cash)) - Decimal(str(session.expected_cash))
    session.closed_at = timezone.now()
    session.save()
    return session
