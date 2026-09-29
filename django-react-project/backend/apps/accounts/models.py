from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from core.models import BaseModel, TenantScopedModel


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    username = models.CharField(max_length=150, unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    tenant_schema = models.CharField(max_length=63, blank=True, default="")
    role = models.CharField(
        max_length=32,
        choices=[
            ("owner", "Owner"),
            ("manager", "Manager"),
            ("cashier", "Cashier"),
            ("platform_admin", "Platform Admin"),
        ],
    )
    pin_hash = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["role"]

    def __str__(self):
        return self.username


class BusinessSettings(TenantScopedModel):
    business_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    kra_pin = models.CharField(max_length=50, blank=True)
    currency = models.CharField(max_length=10, default="KES")
    receipt_header = models.TextField(blank=True)
    receipt_footer = models.TextField(blank=True)
    mpesa_shortcode = models.CharField(max_length=20, blank=True)
    return_window_days = models.IntegerField(default=7)
    max_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=15)
    low_stock_default_threshold = models.IntegerField(default=10)

    def __str__(self):
        return self.business_name
