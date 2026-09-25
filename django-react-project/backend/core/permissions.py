from rest_framework.permissions import BasePermission


class HasRole(BasePermission):
    def __init__(self, *roles):
        self.roles = roles

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return getattr(user, "role", None) in self.roles


class IsCashier(HasRole):
    def __init__(self):
        super().__init__("cashier")


class IsManager(HasRole):
    def __init__(self):
        super().__init__("manager")


class IsOwner(HasRole):
    def __init__(self):
        super().__init__("owner")


class IsPlatformAdmin(HasRole):
    def __init__(self):
        super().__init__("platform_admin")


class ManagerPINVerified(BasePermission):
    def has_permission(self, request, view):
        return bool(getattr(request, "manager_pin_verified", False))
