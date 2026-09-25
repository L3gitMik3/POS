from django.urls import path

from apps.accounts.views import LoginView, LogoutView, MeView, RefreshView, SignupView, UserListCreateView

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/signup/", SignupView.as_view(), name="auth-signup"),
    path("auth/refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("users/", UserListCreateView.as_view(), name="users-list"),
]
