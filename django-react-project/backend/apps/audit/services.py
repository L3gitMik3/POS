from __future__ import annotations

from apps.audit.models import AuditLogEntry


def record(actor, action, model_name, object_id, changes, ip=None):
    return AuditLogEntry.objects.create(
        actor=actor,
        action=action,
        model_name=model_name,
        object_id=str(object_id),
        changes=changes or {},
        ip_address=ip,
    )
