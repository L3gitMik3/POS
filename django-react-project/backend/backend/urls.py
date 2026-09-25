from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_view(request):
    return JsonResponse({"ok": True, "status": "healthy"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_view, name="health"),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.tenants.urls")),
    path("api/v1/inventory/", include("apps.inventory.urls")),
    path("api/v1/sales/", include("apps.sales.urls")),
    path("api/v1/purchasing/", include("apps.purchasing.urls")),
    path("api/v1/payments/", include("apps.payments.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/reports/", include("apps.reporting.urls")),
    path("api/v1/audit/", include("apps.audit.urls")),
]
