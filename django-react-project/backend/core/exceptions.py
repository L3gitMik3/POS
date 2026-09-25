from __future__ import annotations

import logging
import traceback
import uuid

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import exceptions as drf_exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .errors import ERRORS, ErrorCode

logger = logging.getLogger("django")


class AppError(Exception):
    def __init__(self, code, message=None, field=None, details=None, http_status=None):
        default_status, default_message = ERRORS.get(code, (500, "An unexpected error occurred."))
        self.code = code
        self.message = message or default_message
        self.field = field
        self.details = details or {}
        self.http_status = http_status or default_status
        super().__init__(self.message)


class StockInsufficientError(AppError):
    def __init__(self, message=None, field=None, details=None):
        super().__init__(ErrorCode.STOCK_INSUFFICIENT, message, field, details)


class ProductArchivedError(AppError):
    def __init__(self, message=None, field=None, details=None):
        super().__init__(ErrorCode.PRODUCT_ARCHIVED, message, field, details)


class SaleAlreadyVoidedError(AppError):
    def __init__(self, message=None, field=None, details=None):
        super().__init__(ErrorCode.SALE_ALREADY_VOIDED, message, field, details)


class ReturnWindowExpiredError(AppError):
    def __init__(self, message=None, field=None, details=None):
        super().__init__(ErrorCode.RETURN_WINDOW_EXPIRED, message, field, details)


class TillNotOpenError(AppError):
    def __init__(self, message=None, field=None, details=None):
        super().__init__(ErrorCode.TILL_NOT_OPEN, message, field, details)


class TillAlreadyOpenError(AppError):
    def __init__(self, message=None, field=None, details=None):
        super().__init__(ErrorCode.TILL_ALREADY_OPEN, message, field, details)


class DiscountExceedsLimitError(AppError):
    def __init__(self, message=None, field=None, details=None):
        super().__init__(ErrorCode.DISCOUNT_EXCEEDS_LIMIT, message, field, details)


class StaleWriteError(AppError):
    def __init__(self, message=None, field=None, details=None):
        super().__init__(ErrorCode.STALE_WRITE, message, field, details)


class MpesaInitiationFailedError(AppError):
    def __init__(self, message=None, field=None, details=None):
        super().__init__(ErrorCode.MPESA_INITIATION_FAILED, message, field, details)


class TenantSuspendedError(AppError):
    def __init__(self, message=None, field=None, details=None):
        super().__init__(ErrorCode.TENANT_SUSPENDED, message, field, details)


def envelope_exception_handler(exc, context):
    if isinstance(exc, AppError):
        payload = {
            "ok": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "field": exc.field,
                "details": exc.details,
            },
        }
        return Response(payload, status=exc.http_status)

    response = exception_handler(exc, context)
    if response is not None:
        data = response.data
        if isinstance(exc, drf_exceptions.ValidationError):
            payload = {
                "ok": False,
                "error": {
                    "code": "validation_error",
                    "message": "Validation failed.",
                    "field": None,
                    "details": data,
                },
            }
            return Response(payload, status=response.status_code)
        if isinstance(exc, (PermissionDenied, drf_exceptions.NotAuthenticated)):
            payload = {
                "ok": False,
                "error": {
                    "code": "permission_denied",
                    "message": "You do not have permission to perform this action.",
                    "field": None,
                    "details": data,
                },
            }
            return Response(payload, status=response.status_code)
        if isinstance(exc, Http404):
            payload = {
                "ok": False,
                "error": {
                    "code": "not_found",
                    "message": "The requested resource was not found.",
                    "field": None,
                    "details": data,
                },
            }
            return Response(payload, status=response.status_code)

    incident_id = str(uuid.uuid4())
    logger.exception("Unhandled exception: %s", incident_id)
    payload = {
        "ok": False,
        "error": {
            "code": "internal_error",
            "message": "An unexpected error occurred.",
            "field": None,
            "details": {"incident_id": incident_id},
        },
    }
    return Response(payload, status=500)
