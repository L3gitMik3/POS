from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.inventory.services import deduct_sale_stock
from apps.payments.models import MpesaTransaction
from apps.sales.services import void_sale


def initiate_payment(sale, phone_number):
    return MpesaTransaction.objects.create(
        sale=sale,
        phone_number=phone_number,
        amount=sale.total_amount,
        checkout_request_id=f"{sale.id}-checkout",
        status="pending",
    )


def handle_mpesa_callback(checkout_request_id, payload):
    tx = MpesaTransaction.objects.select_related("sale").get(checkout_request_id=checkout_request_id)
    if tx.status in {"completed", "failed", "cancelled"}:
        return tx

    tx.raw_callback = payload
    tx.result_code = str(payload.get("ResultCode", ""))
    tx.result_description = str(payload.get("ResultDesc", ""))

    if payload.get("ResultCode") == "0":
        tx.status = "completed"
        tx.sale.payment_status = "paid"
        tx.sale.save(update_fields=["payment_status", "updated_at"])
        deduct_sale_stock(tx.sale_id, list(tx.sale.lines.values("product_id", "quantity")), tx.sale.cashier)
    else:
        tx.status = "failed"
        tx.sale.payment_status = "failed"
        tx.sale.save(update_fields=["payment_status", "updated_at"])
        void_sale(tx.sale_id, actor=None, override_token=None)

    tx.completed_at = timezone.now()
    tx.save()
    return tx


def reconcile_stale():
    cutoff = timezone.now() - timedelta(minutes=getattr(settings, "MPESA_PENDING_TIMEOUT_MINUTES", 10))
    stale = MpesaTransaction.objects.filter(status="pending", created_at__lt=cutoff)
    for tx in stale:
        tx.status = "failed"
        tx.save(update_fields=["status"])
    return stale.count()
