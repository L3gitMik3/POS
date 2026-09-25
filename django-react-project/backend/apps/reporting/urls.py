from django.urls import path

from apps.reporting.views import CashierReportView, DashboardReportView, DailySnapshotView, SalesReportView

urlpatterns = [
    path("dashboard/", DashboardReportView.as_view()),
    path("sales/", SalesReportView.as_view()),
    path("cashiers/", CashierReportView.as_view()),
    path("daily/", DailySnapshotView.as_view()),
]
