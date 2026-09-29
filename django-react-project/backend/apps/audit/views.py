from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditLogEntry


class AuditListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        entries = AuditLogEntry.objects.select_related("actor").order_by("-created_at")[:200]
        return Response([
            {
                "id": item.id,
                "actor": item.actor.username if item.actor else "System",
                "action": item.action,
                "model_name": item.model_name,
                "object_id": item.object_id,
                "changes": item.changes,
                "ip_address": item.ip_address,
                "created_at": item.created_at,
            }
            for item in entries
        ])
