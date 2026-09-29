from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.text import slugify
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.serializers import TenantTokenObtainPairSerializer
from apps.tenants.models import Tenant

User = get_user_model()


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = TenantTokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        return Response(
            {
                "access": data["access"],
                "refresh": data["refresh"],
                "user_id": data["user_id"],
                "role": data["role"],
                "tenant_schema": data["tenant_schema"],
            },
            status=status.HTTP_200_OK,
        )


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        business_name = str(request.data.get("business_name", "")).strip()
        business_type = str(request.data.get("business_type", "")).strip()
        username = str(request.data.get("username", "")).strip()
        password = request.data.get("password", "")
        schema_base = slugify(business_name).replace("-", "_") or "store"
        schema_name = ""
        for _ in range(10):
            schema_suffix = uuid4().hex[:12]
            schema_name = f"{schema_base[:50]}_{schema_suffix}"
            if not Tenant.objects.filter(schema_name=schema_name).exists():
                break
        else:
            return Response({"detail": "Could not allocate a unique store workspace. Please try again."}, status=503)

        if not business_name or not business_type or not username or len(password) < 8 or not schema_name:
            return Response(
                {"detail": "Business name, business type, username, schema, and an 8-character password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(business_type) > 160:
            return Response({"detail": "Business type must be 160 characters or fewer."}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({"detail": "That username is already registered."}, status=status.HTTP_409_CONFLICT)

        with transaction.atomic():
            tenant = Tenant.objects.create(
                schema_name=schema_name,
                slug=schema_name,
                name=business_name,
                business_type=business_type,
                status="active",
            )
            owner = User.objects.create_user(
                username=username,
                password=password,
                full_name=business_name,
                role="owner",
                is_active=True,
                tenant_schema=tenant.schema_name,
            )

        return Response({"tenant_schema": tenant.schema_name, "business_type": tenant.business_type, "user_id": str(owner.pk), "username": owner.username}, status=status.HTTP_201_CREATED)


class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response({"detail": "Invalid refresh token."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Logged out."}, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        return Response(
            {
                "id": str(user.pk),
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role,
                "tenant_schema": getattr(request.tenant, "schema_name", "public"),
            }
        )


class UserListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        qs = User.objects.filter(is_active=True, tenant_schema=request.tenant.schema_name)
        return Response([
            {
                "id": str(user.pk),
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role,
            }
            for user in qs
        ])

    def post(self, request, *args, **kwargs):
        required_fields = ["username", "password", "role"]
        missing = [field for field in required_fields if not request.data.get(field)]
        if missing:
            return Response({"detail": f"Required fields: {', '.join(missing)}"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=request.data["username"]).exists():
            return Response({"detail": "Username already exists."}, status=status.HTTP_409_CONFLICT)
        user = User.objects.create_user(
            username=request.data["username"], password=request.data["password"],
            full_name=request.data.get("full_name", ""), role=request.data["role"], is_active=True,
            tenant_schema=request.tenant.schema_name,
        )
        return Response({"id": str(user.pk), "username": user.username, "full_name": user.full_name, "role": user.role}, status=status.HTTP_201_CREATED)
