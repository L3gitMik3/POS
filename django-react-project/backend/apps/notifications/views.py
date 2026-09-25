from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import Notification
from apps.notifications.services import mark_read, notify
from core.api import required


def notification_data(item):
    return {"id": item.id, "type": item.type, "message": item.message, "reference_id": item.reference_id, "dedupe_key": item.dedupe_key, "read_at": item.read_at, "created_at": item.created_at}


class NotificationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([notification_data(item) for item in Notification.objects.order_by("-created_at")[:100]])

    def post(self, request):
        error = required(request.data, "type", "message")
        if error:
            return error
        return Response(notification_data(notify(request.data["type"], request.data["message"], request.data.get("reference_id"), request.data.get("dedupe_key"))), status=201)


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        error = required(request.data, "ids")
        if error:
            return error
        mark_read(request.data["ids"], request.user)
        return Response({"ok": True})
