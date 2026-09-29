from __future__ import annotations

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import connection
from django.http import JsonResponse
from django.utils.text import slugify
from django.utils.deprecation import MiddlewareMixin

from apps.tenants.models import Tenant

PUBLIC_PATHS = {
    "/admin/",
    "/health/",
    "/api/v1/auth/login/",
    "/api/v1/auth/signup/",
    "/api/v1/auth/refresh/",
    "/api/v1/payments/mpesa/callback/",
}


def set_public_schema():
    if hasattr(connection, "set_schema_to_public"):
        connection.set_schema_to_public()


def set_tenant_schema(schema_name):
    if hasattr(connection, "set_schema"):
        connection.set_schema(schema_name)


class TenantResolutionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.tenant = None
        path = request.path
        if path in PUBLIC_PATHS:
            set_public_schema()
            return None
        if request.method == "OPTIONS":
            return JsonResponse({}, status=200)

        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return JsonResponse({"detail": "Missing valid bearer token."}, status=403)

        token = auth.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except Exception:  # pragma: no cover - validation path for auth error
            return JsonResponse({"detail": "Invalid or expired token."}, status=403)

        tenant_schema = payload.get("tenant_schema")
        if not tenant_schema or tenant_schema == settings.PUBLIC_SCHEMA_NAME:
            user_id = payload.get("user_id")
            if not user_id:
                return JsonResponse({"detail": "Token is missing a tenant and user claim."}, status=403)

            set_public_schema()
            User = get_user_model()
            try:
                user = User.objects.get(pk=user_id, is_active=True)
            except User.DoesNotExist:
                return JsonResponse({"detail": "Token user not found or inactive."}, status=403)

            tenant_schema = user.tenant_schema or slugify(user.full_name).replace("-", "_")
            if not tenant_schema:
                return JsonResponse({"detail": "Could not determine a tenant for this account."}, status=403)

        set_public_schema()

        try:
            tenant = Tenant.objects.get(schema_name=tenant_schema)
        except Tenant.DoesNotExist:
            return JsonResponse({"detail": "Tenant not found."}, status=403)

        if tenant.status != "active":
            return JsonResponse({"detail": "Tenant is suspended."}, status=403)

        request.tenant = tenant
        set_tenant_schema(tenant_schema)
        return None

    def process_response(self, request, response):
        set_public_schema()
        return response

    def process_exception(self, request, exception):
        set_public_schema()
        if isinstance(exception, PermissionDenied):
            return JsonResponse({"detail": str(exception) or "Forbidden."}, status=403)
        return None
