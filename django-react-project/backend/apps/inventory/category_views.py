from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record
from apps.inventory.models import Category


class CategoryListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([{"id": item.id, "name": item.name, "is_active": item.is_active} for item in Category.objects.filter(is_active=True)])

    def post(self, request):
        name = str(request.data.get("name", "")).strip()
        if not name:
            return Response({"detail": "name is required."}, status=400)
        item = Category.objects.create(name=name, is_active=request.data.get("is_active", True))
        record(request.user, "added", "Category", item.id, {"name": item.name})
        return Response({"id": item.id, "name": item.name, "is_active": item.is_active}, status=201)