from django.urls import path

from apps.tenants.models import Tenant
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class TenantListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenants = Tenant.objects.order_by("name")
        return Response([{"schema_name": item.schema_name, "slug": item.slug, "name": item.name, "status": item.status, "created_on": item.created_on} for item in tenants])

urlpatterns = [
    path("tenants/", TenantListView.as_view()),
]
