from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.payments.services import handle_mpesa_callback, initiate_payment
from apps.sales.models import Sale
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
        transaction = handle_mpesa_callback(request.data["checkout_request_id"], request.data)
        return Response({"checkout_request_id": transaction.checkout_request_id, "status": transaction.status, "result_code": transaction.result_code})
