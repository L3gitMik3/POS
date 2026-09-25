from __future__ import annotations

import jwt
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import connection
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
    if connection.vendor == "postgresql":
        connection.set_schema_to_public()


def set_tenant_schema(schema_name):
    if connection.vendor == "postgresql":
        connection.set_schema(schema_name)


class TenantResolutionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.tenant = None
        path = request.path
        if path in PUBLIC_PATHS:
            set_public_schema()
            return None

        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            raise PermissionDenied("Missing valid bearer token.")

        token = auth.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except Exception as exc:  # pragma: no cover - validation path for auth error
            raise PermissionDenied("Invalid or expired token.") from exc

        tenant_schema = payload.get("tenant_schema")
        if not tenant_schema:
            raise PermissionDenied("Token missing tenant_schema claim.")

        try:
            tenant = Tenant.objects.get(schema_name=tenant_schema)
        except Tenant.DoesNotExist as exc:
            raise PermissionDenied("Tenant not found.") from exc

        if tenant.status != "active":
            raise PermissionDenied("Tenant is suspended.")

        request.tenant = tenant
        set_tenant_schema(tenant_schema)
        return None

    def process_response(self, request, response):
        set_public_schema()
        return response

    def process_exception(self, request, exception):
        set_public_schema()
        return None
