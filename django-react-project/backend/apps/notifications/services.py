from __future__ import annotations

from django.utils import timezone

from apps.notifications.models import Notification


def notify(type, message, reference_id=None, dedupe_key=None):
    if dedupe_key:
        existing = Notification.objects.filter(dedupe_key=dedupe_key).first()
        if existing:
            if existing.message != message:
                existing.message = message
                existing.save(update_fields=["message"])
            return existing
    return Notification.objects.create(
        type=type,
        message=message,
        reference_id=reference_id or "",
        dedupe_key=dedupe_key,
    )


def notify_low_stock(product, current_stock):
    if product.low_stock_threshold <= 0:
        return None
    if current_stock > product.low_stock_threshold:
        Notification.objects.filter(
            type="low_stock",
            reference_id=str(product.pk),
            read_at__isnull=True,
        ).update(read_at=timezone.now())
        return None
    return notify(
        "low_stock",
        f"{product.name} is low on stock ({current_stock} remaining; reorder level {product.low_stock_threshold}).",
        reference_id=str(product.pk),
        dedupe_key=f"low_stock:{product.pk}:{timezone.localdate().isoformat()}",
    )


def mark_read(ids, user):
    Notification.objects.filter(id__in=ids, read_at__isnull=True).update(read_at=timezone.now())
    return True


def unread_count():
    return Notification.objects.filter(read_at__isnull=True).count()


def resolve(dedupe_key):
    Notification.objects.filter(dedupe_key=dedupe_key).update(read_at=timezone.now())
    return True
