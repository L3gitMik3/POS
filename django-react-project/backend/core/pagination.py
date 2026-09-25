from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    page_size = 50
    max_page_size = 200


class LedgerCursorPagination(PageNumberPagination):
    page_size = 50
    max_page_size = 200
