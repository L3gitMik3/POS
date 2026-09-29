from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.utils.text import slugify
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

        if tenant_schema:
            if user.tenant_schema and tenant_schema != user.tenant_schema:
                raise serializers.ValidationError("That tenant does not belong to this account.")
            tenant = Tenant.objects.filter(schema_name=tenant_schema).first()
            if tenant is None:
                raise serializers.ValidationError("Tenant not found.")
        else:
            inferred_schema = user.tenant_schema or slugify(user.full_name).replace("-", "_")
            tenant = Tenant.objects.filter(schema_name=inferred_schema).first()
            if tenant is None:
                raise serializers.ValidationError(
                    "Could not determine a tenant for this account. Contact your administrator."
                )
            tenant_schema = tenant.schema_name

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
