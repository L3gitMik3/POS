from django.db import connection
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.payments.services import handle_mpesa_callback, initiate_payment
from apps.sales.models import Sale
from apps.tenants.models import MpesaCallbackRoute
from core.api import required


class MpesaInitiateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        error = required(request.data, "sale_id", "phone_number")
        if error:
            return error
        transaction = initiate_payment(Sale.objects.get(pk=request.data["sale_id"]), request.data["phone_number"])
        return Response({"id": transaction.id, "checkout_request_id": transaction.checkout_request_id, "status": transaction.status, "amount": str(transaction.amount)}, status=201)


class MpesaCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        error = required(request.data, "checkout_request_id")
        if error:
            return error
        route = MpesaCallbackRoute.objects.filter(checkout_request_id=request.data["checkout_request_id"]).first()
        if route is None:
            return Response({"detail": "Payment callback route not found."}, status=404)
        previous_schema = getattr(connection, "schema_name", "public")
        connection.set_schema(route.tenant_schema)
        try:
            transaction = handle_mpesa_callback(request.data["checkout_request_id"], request.data)
        finally:
            connection.set_schema(previous_schema)
        return Response({"checkout_request_id": transaction.checkout_request_id, "status": transaction.status, "result_code": transaction.result_code})
