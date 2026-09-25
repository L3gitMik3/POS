from rest_framework.views import APIView


class PlatformAdminView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        return self.get_permissions()
