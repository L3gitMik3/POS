from __future__ import annotations

from decimal import Decimal

from rest_framework.response import Response
from rest_framework import status


def decimal_value(value, default="0"):
    return Decimal(str(value if value not in (None, "") else default))


def required(data, *names):
    missing = [name for name in names if data.get(name) in (None, "")]
    if missing:
        return Response({"detail": f"Required fields: {', '.join(missing)}"}, status=status.HTTP_400_BAD_REQUEST)
    return None