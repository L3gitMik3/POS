from __future__ import annotations

from django.utils import timezone

from apps.notifications.models import Notification


def notify(type, message, reference_id=None, dedupe_key=None):
    if dedupe_key:
        existing = Notification.objects.filter(dedupe_key=dedupe_key).first()
        if existing:
            return existing
    return Notification.objects.create(
        type=type,
        message=message,
        reference_id=reference_id or "",
        dedupe_key=dedupe_key,
    )


def mark_read(ids, user):
    Notification.objects.filter(id__in=ids, read_at__isnull=True).update(read_at=timezone.now())
    return True


def unread_count():
    return Notification.objects.filter(read_at__isnull=True).count()


def resolve(dedupe_key):
    Notification.objects.filter(dedupe_key=dedupe_key).update(read_at=timezone.now())
    return True
