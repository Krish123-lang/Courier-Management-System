from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Invoice)
admin.site.register(PaymentMethod)
admin.site.register(ShipmentTracking)


class DeliveryAssignmentInline(admin.TabularInline):
    model = DeliveryAssignment
    extra = 1
    readonly_fields = ("assigned_at",)
    fields = ("delivery_staff", "status", "assigned_by", "assigned_at")


class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("id", "trackingId", "sender_name", "recipientName", "delivery_status", "assigned_delivery_staff")
    inlines = [DeliveryAssignmentInline]

    def assigned_delivery_staff(self, obj):
        latest = obj.assignments.order_by("-assigned_at").first()
        return latest.delivery_staff.email if latest and latest.delivery_staff else "-"
    assigned_delivery_staff.short_description = "Delivery Staff"


class DeliveryAssignmentAdmin(admin.ModelAdmin):
    list_display = ("shipment", "delivery_staff", "assigned_by", "status", "assigned_at")
    list_filter = ("status", "delivery_staff")
    search_fields = ("shipment__trackingId", "delivery_staff__email")


admin.site.register(DeliveryAssignment, DeliveryAssignmentAdmin)
admin.site.register(Shipment, ShipmentAdmin)


class ReviewUserAdmin(admin.ModelAdmin):
    list_display = ("booking", "star", "date")
admin.site.register(ReviewUser, ReviewUserAdmin)
