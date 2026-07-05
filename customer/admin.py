from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Invoice)
admin.site.register(PaymentMethod)
admin.site.register(ShipmentTracking)
admin.site.register(DeliveryAssignment)

class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("id", "trackingId", "sender_name", "recipientName", "delivery_status")
admin.site.register(Shipment, ShipmentAdmin)


class ReviewUserAdmin(admin.ModelAdmin):
    list_display = ("booking", "star", "date")
admin.site.register(ReviewUser, ReviewUserAdmin)
