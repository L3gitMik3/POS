from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import F

from apps.audit.services import record
from apps.inventory.services import record_movement
from apps.purchasing.models import GoodsReceivedNote, GRNLine, PurchaseOrder, PurchaseOrderLine


def create_purchase_order(supplier, created_by, lines, expected_date=None):
    with transaction.atomic():
        po = PurchaseOrder.objects.create(
            supplier=supplier,
            created_by=created_by,
            status="draft",
            expected_date=expected_date,
        )
        for line in lines:
            PurchaseOrderLine.objects.create(
                purchase_order=po,
                product_id=line["product_id"],
                quantity_ordered=int(line["quantity_ordered"]),
                unit_cost=line.get("unit_cost", 0),
            )
        record(
            created_by,
            "added",
            "PurchaseOrder",
            po.id,
            {"supplier": supplier.name, "line_count": len(lines), "expected_date": str(expected_date or "")},
        )
    return po


def receive_goods(po_id, lines, actor, delivery_note_ref=""):
    with transaction.atomic():
        po = PurchaseOrder.objects.select_for_update().get(id=po_id)
        if po.status in {"cancelled", "fully_received"}:
            raise ValueError(f"Cannot receive goods for a {po.status.replace('_', ' ')} order.")
        grn = GoodsReceivedNote.objects.create(
            purchase_order=po,
            received_by=actor,
            delivery_note_ref=delivery_note_ref,
        )
        received_summary = []
        for line in lines:
            quantity = int(line["quantity_received"])
            if quantity <= 0:
                raise ValueError("Received quantities must be greater than zero.")
            order_line = po.lines.select_for_update().get(product_id=line["product_id"])
            if order_line.quantity_received_so_far + quantity > order_line.quantity_ordered:
                raise ValueError("Over receipt rejected")
            order_line.quantity_received_so_far += quantity
            order_line.save(update_fields=["quantity_received_so_far"])
            GRNLine.objects.create(
                grn=grn,
                product_id=line["product_id"],
                quantity_received=quantity,
                unit_cost=order_line.unit_cost,
            )
            record_movement(
                product_id=line["product_id"],
                delta=quantity,
                reason="purchase",
                reference_id=None,
                actor=actor,
            )
            received_summary.append({"product_id": str(line["product_id"]), "quantity": quantity})
        po.status = "fully_received" if po.lines.filter(quantity_received_so_far__lt=F("quantity_ordered")).exists() is False else "partially_received"
        po.save(update_fields=["status"])
        record(
            actor,
            "received",
            "PurchaseOrder",
            po.id,
            {"grn_id": grn.id, "delivery_note_ref": delivery_note_ref, "lines": received_summary},
        )
    return po
