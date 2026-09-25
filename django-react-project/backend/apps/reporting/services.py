from __future__ import annotations

from django.utils import timezone
from django.db.models import Sum

from apps.sales.models import Sale


def build_daily_snapshot(date):
    qs = Sale.objects.filter(created_at__date=date)
    return {
        "date": str(date),
        "gross_sales": qs.aggregate(total=Sum("total_amount"))["total"] or 0,
        "transaction_count": qs.count(),
    }


def dashboard_summary():
    today = timezone.now().date()
    return {
        "sales_today": Sale.objects.filter(created_at__date=today).count(),
        "gross_sales": Sale.objects.filter(created_at__date=today).aggregate(total=Sum("total_amount"))["total"] or 0,
    }


def sales_report(start, end, group_by):
    return list(Sale.objects.filter(created_at__range=[start, end]).values(group_by).annotate(total=Sum("total_amount")))


def inventory_valuation():
    return []


def cashier_performance(start, end):
    return list(Sale.objects.filter(created_at__range=[start, end]).values("cashier__username").annotate(total=Sum("total_amount")))
