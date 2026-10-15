from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.tenants.models import Tenant


class TenantTokenObtainPairSerializer(TokenObtainPairSerializer):
    tenant_schema = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")
        tenant_schema = attrs.get("tenant_schema")

        user = authenticate(username=username, password=password)
        if user is None or not user.is_active:
            raise serializers.ValidationError("Invalid credentials.")

        assigned_schema = user.tenant_schema
        if not assigned_schema:
            raise serializers.ValidationError("This account is not assigned to a tenant workspace.")
        if tenant_schema and tenant_schema != assigned_schema:
            raise serializers.ValidationError("That tenant does not belong to this account.")
        tenant_schema = assigned_schema
        tenant = Tenant.objects.filter(schema_name=tenant_schema).first()
        if tenant is None:
            raise serializers.ValidationError(
                "Could not determine a tenant for this account. Contact your administrator."
            )

        if tenant.status != "active":
            raise serializers.ValidationError("Tenant is not active.")

        data = super().validate({"username": username, "password": password})
        refresh = self.get_token(user)
        refresh["tenant_schema"] = tenant_schema
        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
        data["tenant_schema"] = tenant_schema
        data["user_id"] = str(user.pk)
        data["role"] = user.role
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["user_id"] = str(user.pk)
        return token


class TenantTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = RefreshToken(attrs["refresh"])
        access = AccessToken(data["access"])
        for claim in ("tenant_schema", "role", "user_id"):
            if claim in refresh:
                access[claim] = refresh[claim]
        data["access"] = str(access)
        return data


class UserSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    username = serializers.CharField()
    full_name = serializers.CharField(required=False, allow_blank=True)
    role = serializers.CharField()


class BusinessSettingsSerializer(serializers.Serializer):
    business_name = serializers.CharField(required=False, allow_blank=True)
    currency = serializers.CharField(required=False, allow_blank=True)


class PinVerifySerializer(serializers.Serializer):
    pin = serializers.CharField(write_only=True)
