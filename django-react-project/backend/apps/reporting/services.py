from __future__ import annotations

import calendar
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate, TruncHour, TruncMonth
from django.utils import timezone

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


def build_period_report(period, today=None):
    """Return totals and a zero-filled time series for a selected reporting period.

    daily: today by hour; weekly: current Monday–Sunday week; monthly: current
    calendar month by day; yearly: current calendar year by month.
    """
    today = today or timezone.localdate()
    if period == "daily":
        start_date, end_date, bucket = today, today, "hour"
        bucket_count = 24
        start_at = timezone.make_aware(datetime.combine(today, time.min))
        end_at = start_at + timedelta(days=1)
        trunc_expression = TruncHour("created_at", tzinfo=timezone.get_current_timezone())
        bucket_keys = [start_at + timedelta(hours=index) for index in range(bucket_count)]
        key = lambda value: timezone.localtime(value).replace(minute=0, second=0, microsecond=0)
        label = lambda value: timezone.localtime(value).strftime("%I %p").lstrip("0")
    elif period == "weekly":
        start_date = today - timedelta(days=today.weekday())
        end_date, bucket = start_date + timedelta(days=6), "day"
        start_at = timezone.make_aware(datetime.combine(start_date, time.min))
        end_at = timezone.make_aware(datetime.combine(end_date + timedelta(days=1), time.min))
        trunc_expression = TruncDate("created_at", tzinfo=timezone.get_current_timezone())
        bucket_keys = [start_date + timedelta(days=index) for index in range(7)]
        key = lambda value: value
        label = lambda value: value.strftime("%a %d")
    elif period == "monthly":
        start_date = today.replace(day=1)
        end_date = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
        bucket = "day"
        start_at = timezone.make_aware(datetime.combine(start_date, time.min))
        end_at = timezone.make_aware(datetime.combine(end_date + timedelta(days=1), time.min))
        trunc_expression = TruncDate("created_at", tzinfo=timezone.get_current_timezone())
        bucket_keys = [start_date + timedelta(days=index) for index in range(end_date.day)]
        key = lambda value: value
        label = lambda value: value.strftime("%d %b")
    elif period == "yearly":
        first_month = date(today.year, 1, 1)
        start_date, end_date, bucket = first_month, date(today.year, 12, 31), "month"
        start_at = timezone.make_aware(datetime.combine(first_month, time.min))
        end_at = timezone.make_aware(datetime.combine(end_date + timedelta(days=1), time.min))
        trunc_expression = TruncMonth("created_at", tzinfo=timezone.get_current_timezone())
        bucket_keys = [date(today.year, month, 1) for month in range(1, 13)]
        key = lambda value: value.date().replace(day=1) if isinstance(value, datetime) else value
        label = lambda value: value.strftime("%b %Y")
    else:
        raise ValueError("period must be daily, weekly, monthly, or yearly")

    paid_sales = Sale.objects.filter(
        created_at__gte=start_at,
        created_at__lt=end_at,
        status="completed",
        payment_status="paid",
    )
    aggregates = paid_sales.annotate(bucket=trunc_expression).values("bucket").annotate(
        revenue=Sum("total_amount"),
        transactions=Count("id"),
    ).order_by("bucket")
    by_bucket = {key(row["bucket"]): row for row in aggregates}

    series = [
        {
            "date": bucket_key.isoformat(),
            "label": label(bucket_key),
            "revenue": str(by_bucket.get(bucket_key, {}).get("revenue") or Decimal("0.00")),
            "transactions": by_bucket.get(bucket_key, {}).get("transactions", 0),
        }
        for bucket_key in bucket_keys
    ]
    totals = paid_sales.aggregate(
        revenue=Sum("total_amount"),
        transactions=Count("id"),
        cash_revenue=Sum("total_amount", filter=Q(payment_method="cash")),
        mpesa_revenue=Sum("total_amount", filter=Q(payment_method="mpesa")),
    )
    return {
        "period": period,
        "bucket": bucket,
        "start": start_date.isoformat(),
        "end": end_date.isoformat(),
        "summary": {
            "revenue": str(totals["revenue"] or Decimal("0.00")),
            "transactions": totals["transactions"],
            "average_sale": str((totals["revenue"] or Decimal("0.00")) / totals["transactions"] if totals["transactions"] else Decimal("0.00")),
            "cash_revenue": str(totals["cash_revenue"] or Decimal("0.00")),
            "mpesa_revenue": str(totals["mpesa_revenue"] or Decimal("0.00")),
        },
        "series": series,
    }
