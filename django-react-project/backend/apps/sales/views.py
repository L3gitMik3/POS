from decimal import Decimal

from django.db.models import Count, Q, Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record
from apps.sales.models import Customer, Sale, TillSession
from apps.sales.services import close_till, create_sale, open_till, process_return, void_sale
from core.api import required


def sale_data(sale):
    return {"id": str(sale.id), "receipt_number": sale.receipt_number, "created_at": sale.created_at, "status": sale.status, "payment_status": sale.payment_status, "payment_method": sale.payment_method, "subtotal": str(sale.subtotal), "discount_amount": str(sale.discount_amount), "tax_amount": str(sale.tax_amount), "total_amount": str(sale.total_amount), "cashier": str(sale.cashier_id), "till_session": sale.till_session_id}


def client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    return forwarded_for.split(",", 1)[0].strip() if forwarded_for else request.META.get("REMOTE_ADDR")


class SaleListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([sale_data(sale) for sale in Sale.objects.order_by("-created_at")[:100]])

    def post(self, request):
        error = required(request.data, "cart_lines", "till_session", "payment_method")
        if error:
            return error
        cart_lines = request.data["cart_lines"]
        if not isinstance(cart_lines, list) or not cart_lines:
            return Response({"detail": "cart_lines must contain at least one item."}, status=400)
        for line in cart_lines:
            if not isinstance(line, dict) or not all(field in line for field in ("product_id", "quantity", "unit_price")):
                return Response({"detail": "Each cart line requires product_id, quantity, and unit_price."}, status=400)
            try:
                if int(line["quantity"]) <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                return Response({"detail": "Sale quantities must be positive whole numbers."}, status=400)
        till_session = TillSession.objects.filter(pk=request.data["till_session"], closed_at__isnull=True).first()
        if not till_session:
            return Response({"detail": "An open till session is required."}, status=400)
        customer_phone = str(request.data.get("customer") or "").strip()
        customer = Customer.objects.filter(phone_number=customer_phone).first() if customer_phone else None
        try:
            sale = create_sale(cart_lines, request.user, till_session, request.data["payment_method"], customer=customer, discount=request.data.get("discount"))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(sale_data(sale), status=201)


class CustomerListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        customers = Customer.objects.annotate(
            sales_count=Count("sales", filter=Q(sales__status="completed")),
            total_spent=Sum(
                "sales__total_amount",
                filter=Q(sales__status="completed", sales__payment_status="paid"),
            ),
        ).order_by("name")
        return Response([
            {
                "id": customer.id,
                "name": customer.name,
                "phone_number": customer.phone_number,
                "loyalty_points": customer.loyalty_points,
                "sales_count": customer.sales_count,
                "total_spent": str(customer.total_spent or 0),
            }
            for customer in customers
        ])

    def post(self, request):
        error = required(request.data, "name", "phone_number")
        if error:
            return error
        name = str(request.data["name"]).strip()
        phone_number = str(request.data["phone_number"]).strip()
        if not name or not phone_number:
            return Response({"detail": "Customer name and phone number cannot be blank."}, status=400)
        customer, created = Customer.objects.get_or_create(
            phone_number=phone_number,
            defaults={"name": name},
        )
        if not created and customer.name != name:
            customer.name = name
            customer.save(update_fields=["name"])
        record(
            request.user,
            "added" if created else "updated",
            "Customer",
            customer.id,
            {"name": customer.name, "phone_number": customer.phone_number},
            client_ip(request),
        )
        return Response(
            {
                "id": customer.id,
                "name": customer.name,
                "phone_number": customer.phone_number,
                "loyalty_points": customer.loyalty_points,
            },
            status=201 if created else 200,
        )


class TillOpenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        error = required(request.data, "terminal_id")
        if error:
            return error
        existing = TillSession.objects.filter(terminal_id=request.data["terminal_id"], closed_at__isnull=True).first()
        if existing:
            return Response({"id": existing.id, "terminal_id": existing.terminal_id, "opening_float": str(existing.opening_float), "open": True, "already_open": True}, status=200)
        try:
            session = open_till(request.user, request.data["terminal_id"], request.data.get("float_amount", 0))
        except ValueError as exc:
            return Response({"detail": str(exc), "code": "till_already_open"}, status=409)
        record(
            request.user,
            "open",
            "TillSession",
            session.id,
            {"terminal_id": session.terminal_id, "opening_float": str(session.opening_float)},
            client_ip(request),
        )
        return Response({"id": session.id, "terminal_id": session.terminal_id, "opening_float": str(session.opening_float)}, status=201)


class TillCurrentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        session = TillSession.objects.filter(closed_at__isnull=True).order_by("-opened_at").first()
        if not session:
            return Response({"id": None, "open": False})
        return Response({"id": session.id, "open": True, "terminal_id": session.terminal_id, "opening_float": str(session.opening_float), "opened_at": session.opened_at})


class TillHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = (
            TillSession.objects.select_related("opened_by", "closed_by")
            .annotate(
                sales_count=Count("sales", filter=Q(sales__status="completed")),
                cash_sales_total=Sum(
                    "sales__total_amount",
                    filter=Q(
                        sales__status="completed",
                        sales__payment_method="cash",
                        sales__payment_status="paid",
                    ),
                ),
            )
            .order_by("-opened_at")
        )

        return Response([
            {
                "id": session.id,
                "terminal_id": session.terminal_id,
                "status": "closed" if session.closed_at else "open",
                "opened_at": session.opened_at,
                "opened_by": session.opened_by.username,
                "opening_float": str(session.opening_float),
                "closed_at": session.closed_at,
                "closed_by": session.closed_by.username if session.closed_by else None,
                "sales_count": session.sales_count,
                "cash_sales_total": str(session.cash_sales_total or Decimal("0.00")),
                "counted_cash": str(session.counted_cash) if session.closed_at else None,
                "expected_cash": str(
                    session.expected_cash
                    if session.closed_at
                    else session.opening_float + (session.cash_sales_total or Decimal("0.00"))
                ),
                "variance": str(session.variance) if session.closed_at else None,
            }
            for session in sessions
        ])


class TillCloseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        error = required(request.data, "session_id", "counted_cash")
        if error:
            return error
        session = TillSession.objects.filter(pk=request.data["session_id"], closed_at__isnull=True).first()
        if not session:
            return Response({"detail": "Open till session not found."}, status=404)
        session = close_till(
            session,
            request.data["counted_cash"],
            closed_by=request.user,
        )
        record(
            request.user,
            "close",
            "TillSession",
            session.id,
            {"terminal_id": session.terminal_id, "counted_cash": str(session.counted_cash), "expected_cash": str(session.expected_cash), "variance": str(session.variance)},
            client_ip(request),
        )
        return Response({"id": session.id, "closed_at": session.closed_at, "expected_cash": str(session.expected_cash), "variance": str(session.variance)})


class SaleVoidView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, sale_id):
        return Response(sale_data(void_sale(sale_id, request.user, request.data.get("override_token"))))


class ReturnCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response(process_return(request.data, actor=request.user), status=201)