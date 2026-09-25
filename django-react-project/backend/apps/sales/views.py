from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.sales.models import Customer, Sale, TillSession
from apps.sales.services import close_till, create_sale, open_till, process_return, void_sale
from core.api import required


def sale_data(sale):
    return {"id": str(sale.id), "receipt_number": sale.receipt_number, "status": sale.status, "payment_status": sale.payment_status, "payment_method": sale.payment_method, "subtotal": str(sale.subtotal), "discount_amount": str(sale.discount_amount), "tax_amount": str(sale.tax_amount), "total_amount": str(sale.total_amount), "cashier": str(sale.cashier_id), "till_session": sale.till_session_id}


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
            if not all(field in line for field in ("product_id", "quantity", "unit_price")):
                return Response({"detail": "Each cart line requires product_id, quantity, and unit_price."}, status=400)
        till_session = TillSession.objects.filter(pk=request.data["till_session"], closed_at__isnull=True).first()
        if not till_session:
            return Response({"detail": "An open till session is required."}, status=400)
        customer = Customer.objects.filter(phone_number=request.data.get("customer")).first() if request.data.get("customer") else None
        try:
            sale = create_sale(cart_lines, request.user, till_session, request.data["payment_method"], customer=customer, discount=request.data.get("discount"))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(sale_data(sale), status=201)


class CustomerListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {
                "id": customer.id,
                "name": customer.name,
                "phone_number": customer.phone_number,
                "loyalty_points": customer.loyalty_points,
            }
            for customer in Customer.objects.order_by("name")
        ])

    def post(self, request):
        error = required(request.data, "name", "phone_number")
        if error:
            return error
        customer, created = Customer.objects.get_or_create(
            phone_number=str(request.data["phone_number"]).strip(),
            defaults={"name": str(request.data["name"]).strip()},
        )
        if not created and request.data.get("name"):
            customer.name = str(request.data["name"]).strip()
            customer.save(update_fields=["name"])
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
        return Response({"id": session.id, "terminal_id": session.terminal_id, "opening_float": str(session.opening_float)}, status=201)


class TillCurrentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        session = TillSession.objects.filter(closed_at__isnull=True).order_by("-opened_at").first()
        if not session:
            return Response({"id": None, "open": False})
        return Response({"id": session.id, "open": True, "terminal_id": session.terminal_id, "opening_float": str(session.opening_float), "opened_at": session.opened_at})


class TillCloseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        error = required(request.data, "session_id", "counted_cash")
        if error:
            return error
        session = close_till(TillSession.objects.get(pk=request.data["session_id"]), request.data["counted_cash"])
        return Response({"id": session.id, "closed_at": session.closed_at, "expected_cash": str(session.expected_cash), "variance": str(session.variance)})


class SaleVoidView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, sale_id):
        return Response(sale_data(void_sale(sale_id, request.user, request.data.get("override_token"))))


class ReturnCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response(process_return(request.data, actor=request.user), status=201)