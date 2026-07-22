from django.contrib import admin
from .models import *

# Register your models here.

class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_id", "user", "booking", "amount", "status", "created_at", "pdf")
    list_filter = ("status", "created_at")
    search_fields = ("invoice_id", "user__name", "user__email")
admin.site.register(Invoice, InvoiceAdmin)

class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ("user", "method_type", "upi_id", "is_default", "created_at")
    list_filter = ("method_type", "is_default")
admin.site.register(PaymentMethod, PaymentMethodAdmin)

class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("id", "trackingId", "sender_name", "recipientName", "delivery_status", "get_payment_status")
    search_fields = ("trackingId", "sender_name", "recipientName")
admin.site.register(Shipment, ShipmentAdmin)


class ReviewUserAdmin(admin.ModelAdmin):
    list_display = ("booking", "star", "date")
admin.site.register(ReviewUser, ReviewUserAdmin)
