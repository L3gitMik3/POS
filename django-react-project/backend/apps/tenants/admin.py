from django.contrib import admin

from .models import Domain, MpesaCallbackRoute, Tenant

admin.site.register(Tenant)
admin.site.register(Domain)
admin.site.register(MpesaCallbackRoute)
