class ErrorCode:
    STOCK_INSUFFICIENT = "stock_insufficient"
    PRODUCT_ARCHIVED = "product_archived"
    SALE_ALREADY_VOIDED = "sale_already_voided"
    RETURN_WINDOW_EXPIRED = "return_window_expired"
    TILL_NOT_OPEN = "till_not_open"
    TILL_ALREADY_OPEN = "till_already_open"
    DISCOUNT_EXCEEDS_LIMIT = "discount_exceeds_limit"
    STALE_WRITE = "stale_write"
    MPESA_INITIATION_FAILED = "mpesa_initiation_failed"
    TENANT_SUSPENDED = "tenant_suspended"


ERRORS = {
    ErrorCode.STOCK_INSUFFICIENT: (409, "Not enough stock available."),
    ErrorCode.PRODUCT_ARCHIVED: (409, "This product is archived."),
    ErrorCode.SALE_ALREADY_VOIDED: (409, "This sale has already been voided."),
    ErrorCode.RETURN_WINDOW_EXPIRED: (400, "The return window has expired."),
    ErrorCode.TILL_NOT_OPEN: (409, "No till is currently open."),
    ErrorCode.TILL_ALREADY_OPEN: (409, "A till is already open on this terminal."),
    ErrorCode.DISCOUNT_EXCEEDS_LIMIT: (400, "Discount exceeds the allowed limit."),
    ErrorCode.STALE_WRITE: (409, "The record was modified by another request."),
    ErrorCode.MPESA_INITIATION_FAILED: (502, "M-Pesa initiation failed."),
    ErrorCode.TENANT_SUSPENDED: (403, "This tenant is suspended."),
}
