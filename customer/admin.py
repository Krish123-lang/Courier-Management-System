from django.contrib import admin
from .models import *

# Register your models here.

class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("id", "trackingId", "sender_name", "recipientName", "delivery_status")
admin.site.register(Shipment, ShipmentAdmin)


