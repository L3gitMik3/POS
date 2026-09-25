from __future__ import annotations

from functools import wraps

from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response

from core.models import IdempotencyKey


def idempotent(endpoint_name):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(view, request, *args, **kwargs):
            key = request.headers.get("Idempotency-Key")
            if not key:
                return Response({"detail": "Idempotency-Key header is required."}, status=status.HTTP_400_BAD_REQUEST)

            obj, created = IdempotencyKey.objects.get_or_create(
                key=key,
                defaults={
                    "endpoint": endpoint_name,
                    "response_snapshot": {},
                },
            )

            if not created:
                return Response(obj.response_snapshot, status=status.HTTP_200_OK)

            with transaction.atomic():
                response = view_func(view, request, *args, **kwargs)
                if hasattr(response, "data"):
                    obj.response_snapshot = response.data
                    obj.endpoint = endpoint_name
                    obj.save(update_fields=["endpoint", "response_snapshot"])
                    response.headers["X-Idempotent-Replay"] = "true"
                    return response
                obj.response_snapshot = {"ok": True}
                obj.save(update_fields=["endpoint", "response_snapshot"])
                return response

        return wrapped_view

    return decorator
