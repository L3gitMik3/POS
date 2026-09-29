from datetime import date

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reporting.services import build_daily_snapshot, build_period_report, cashier_performance, dashboard_summary, sales_report


class DashboardReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(dashboard_summary())


class SalesReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        period = request.query_params.get("period")
        if period:
            if period not in {"daily", "weekly", "monthly", "yearly"}:
                return Response({"detail": "period must be daily, weekly, monthly, or yearly."}, status=400)
            return Response(build_period_report(period))
        start = request.query_params.get("start", str(timezone.now().date()))
        end = request.query_params.get("end", str(timezone.now().date()))
        group_by = request.query_params.get("group_by", "payment_method")
        allowed = {"payment_method", "status", "cashier_id"}
        if group_by not in allowed:
            return Response({"detail": "Invalid group_by."}, status=400)
        return Response(sales_report(start, end, group_by))


class CashierReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        return Response(cashier_performance(request.query_params.get("start", str(today)), request.query_params.get("end", str(today))))


class DailySnapshotView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(build_daily_snapshot(request.query_params.get("date", str(timezone.now().date()))))
