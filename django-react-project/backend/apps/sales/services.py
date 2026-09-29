from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.audit.services import record
from apps.inventory.models import Product
from apps.inventory.services import deduct_sale_stock, reverse_movements
from apps.sales.models import Sale, SaleLine, TillSession


def compute_totals(cart_lines, discount):
    subtotal = sum((Decimal(str(line["quantity"])) * Decimal(str(line["unit_price"]))) for line in cart_lines)
    discount_value = Decimal(str(discount or 0))
    tax_total = sum((Decimal(str(line["quantity"])) * Decimal(str(line["unit_price"])) * Decimal(str(line.get("tax_rate", 0))) / Decimal("100")) for line in cart_lines)
    total = subtotal - discount_value + tax_total
    return {"subtotal": subtotal, "discount_amount": discount_value, "tax_amount": tax_total, "total_amount": total}


def create_sale(cart_lines, cashier, till_session, payment_method, customer=None, discount=None, override_token=None):
    with transaction.atomic():
        if payment_method not in {"cash", "mpesa"}:
            raise ValueError("Payment method must be cash or mpesa.")
        priced_lines = []
        for line in cart_lines:
            try:
                quantity = int(line["quantity"])
                product = Product.objects.get(pk=line["product_id"], is_archived=False)
            except (KeyError, Product.DoesNotExist, TypeError, ValueError, ValidationError):
                raise ValueError("One or more selected products are unavailable.") from None
            if quantity <= 0:
                raise ValueError("Sale quantities must be greater than zero.")
            priced_lines.append({
                "product_id": product.id,
                "product_name": product.name,
                "quantity": quantity,
                "unit_price": product.sale_price,
                "tax_rate": product.tax_rate,
            })

        totals = compute_totals(priced_lines, discount)
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

        for line in priced_lines:
            SaleLine.objects.create(
                sale=sale,
                product_id=line["product_id"],
                quantity=line["quantity"],
                unit_price=line["unit_price"],
                tax_rate=line.get("tax_rate", 0),
                line_total=Decimal(str(line["quantity"])) * Decimal(str(line["unit_price"])),
            )

        if payment_method == "cash":
            deduct_sale_stock(sale.id, priced_lines, cashier)
        record(
            cashier,
            "sold",
            "Sale",
            sale.id,
            {
                "receipt_number": sale.receipt_number,
                "total_amount": str(sale.total_amount),
                "payment_method": payment_method,
                "items": [
                    {"product": line["product_name"], "quantity": line["quantity"], "unit_price": str(line["unit_price"])}
                    for line in priced_lines
                ],
            },
        )
    return sale


def void_sale(sale_id, actor, override_token):
    with transaction.atomic():
        sale = Sale.objects.select_for_update().get(id=sale_id)
        if sale.status == "voided":
            raise ValueError("Sale already voided")
        was_paid = sale.payment_status == "paid"
        sale.status = "voided"
        sale.payment_status = "failed"
        sale.save(update_fields=["status", "payment_status", "updated_at"])
        if was_paid:
            reverse_movements(sale.id, "sale_void", actor)
        record(actor, "sale_voided", "Sale", sale.id, {"receipt_number": sale.receipt_number, "stock_restored": was_paid})
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


def close_till(session, counted_cash, closed_by=None):
    session.counted_cash = counted_cash
    cash_sales = session.sales.filter(
        status="completed",
        payment_method="cash",
        payment_status="paid",
    ).aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
    session.expected_cash = session.opening_float + cash_sales
    session.variance = Decimal(str(counted_cash)) - Decimal(str(session.expected_cash))
    session.closed_at = timezone.now()
    if closed_by is not None:
        session.closed_by = closed_by
    session.save()
    return session
