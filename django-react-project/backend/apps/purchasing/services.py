from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import F

from apps.inventory.services import record_movement
from apps.purchasing.models import PurchaseOrder, PurchaseOrderLine


def create_purchase_order(supplier, created_by, lines):
    po = PurchaseOrder.objects.create(supplier=supplier, created_by=created_by, status="draft")
    for line in lines:
        PurchaseOrderLine.objects.create(
            purchase_order=po,
            product_id=line["product_id"],
            quantity_ordered=line["quantity_ordered"],
            unit_cost=line.get("unit_cost", 0),
        )
    return po


def receive_goods(po_id, lines, actor):
    po = PurchaseOrder.objects.get(id=po_id)
    with transaction.atomic():
        for line in lines:
            order_line = po.lines.get(product_id=line["product_id"])
            if order_line.quantity_received_so_far + line["quantity_received"] > order_line.quantity_ordered:
                raise ValueError("Over receipt rejected")
            order_line.quantity_received_so_far += line["quantity_received"]
            order_line.save(update_fields=["quantity_received_so_far"])
            record_movement(
                product_id=line["product_id"],
                delta=line["quantity_received"],
                reason="purchase",
                reference_id=po.id,
                actor=actor,
            )
        po.status = "fully_received" if po.lines.filter(quantity_received_so_far__lt=F("quantity_ordered")).exists() is False else "partially_received"
        po.save(update_fields=["status"])
    return po
