from django.db import models
from django.utils import timezone
from main.models import *
import string, random

# Create your models here.


def generate_trackingId():
    ch = string.ascii_uppercase + string.digits
    return "".join(random.choice(ch) for _ in range(10))

class ShipmentStatusHistory(models.Model):
    shipment = models.ForeignKey('Shipment', related_name='status_history', on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['timestamp', 'id']

    def __str__(self):
        return f"{self.shipment.trackingId or self.shipment.id} - {self.status}"


class Shipment(models.Model):
    # status_choices = (
    #     ('Pending', 'Pending'),
    #     ('out', 'OUT FOR DELIVERY'),
    #     ('hub', 'AT HUB'),
    #     ('depart', 'DEPARTED'),
    #     ('delivered', 'DELIVERED'),
    #     ('cancelled', 'CANCELLED'),
    # )
    
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('AT_HUB', 'At Hub'),
        ('OUT_FOR_DELIVERY', 'Out For Delivery'),
        ('DEPARTED', 'Departed'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    )
    
    customerid = models.ForeignKey(sign, on_delete=models.CASCADE, null=True, blank=True)
    trackingId = models.CharField(max_length=20, default = generate_trackingId, unique=True, null=True)
    delivery_status = models.CharField(max_length=50, default="Pending", choices=STATUS_CHOICES, null=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    status_updated_at = models.DateTimeField(null=True, blank=True)
    current_location = models.CharField(max_length=100, null=True, blank=True)
    sender_name = models.CharField(max_length=100, null=True)
    pickupAddress = models.TextField(null=True)
    senderNumber = models.CharField(max_length=15, null=True)
    recipientName = models.CharField(max_length=100, null=True)
    recipientAddress = models.TextField(null=True)
    recipientNumber = models.CharField(max_length=15, null=True)
    package_description = models.CharField(max_length=100, null=True)
    service_type = models.CharField(max_length=100, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    def __str__(self):
        return str(self.trackingId or self.id)

    @staticmethod
    def normalize_delivery_status(value):
        if value is None:
            return "PENDING"
        normalized = str(value).strip().upper().replace(" ", "_")
        return {
            "PENDING": "PENDING",
            "AT_HUB": "AT_HUB",
            "OUT_FOR_DELIVERY": "OUT_FOR_DELIVERY",
            "DEPARTED": "DEPARTED",
            "DELIVERED": "DELIVERED",
            "CANCELLED": "CANCELLED",
        }.get(normalized, normalized)

    def get_tracking_history(self):
        current_status = str(self.delivery_status or "PENDING").upper()

        if current_status == "CANCELLED":
            return [{
                "title": "Order has been cancelled",
                "description": self.recipientAddress or "The shipment has been cancelled.",
                "icon_class": "fas fa-box-open text-muted",
                "badge_class": "bg-dark",
                "status": "CANCELLED",
                "timestamp": None,
            }]

        status_rank = {
            "PENDING": 0,
            "AT_HUB": 1,
            "OUT_FOR_DELIVERY": 2,
            "DEPARTED": 3,
            "DELIVERED": 4,
        }
        current_rank = status_rank.get(current_status, 0)

        steps = [
            {
                "title": "Order Placed",
                "description": "Your shipment request has been received and is being processed.",
                "icon_class": "fas fa-check text-success",
                "badge_class": "bg-success",
                "status": "PENDING",
            },
            {
                "title": "Arrived at Destination Hub",
                "description": self.current_location or "Destination hub update pending.",
                "icon_class": "fas fa-truck-loading text-info",
                "badge_class": "bg-info",
                "status": "AT_HUB",
            },
            {
                "title": "Out for Delivery",
                "description": f"Local Distribution Center, {self.current_location or 'processing center'}",
                "icon_class": "fas fa-check text-success",
                "badge_class": "bg-success",
                "status": "OUT_FOR_DELIVERY",
            },
            {
                "title": "Departed from Origin Hub",
                "description": self.current_location or "Origin hub update pending.",
                "icon_class": "fas fa-plane text-secondary",
                "badge_class": "bg-secondary",
                "status": "DEPARTED",
            },
            {
                "title": "Shipment Picked Up",
                "description": self.recipientAddress or "Recipient details pending.",
                "icon_class": "fas fa-box-open text-muted",
                "badge_class": "bg-dark",
                "status": "DELIVERED",
            },
        ]

        history = []
        for step in steps:
            if status_rank.get(step["status"], 0) <= current_rank:
                history_entry = self.status_history.filter(status=step["status"]).order_by('-timestamp').first()
                history.append({
                    **step,
                    "timestamp": history_entry.timestamp if history_entry else (self.created_at if step["status"] == "PENDING" else None),
                })

        return history

    def save(self, *args, **kwargs):
        self.delivery_status = self.normalize_delivery_status(self.delivery_status)

        is_new = self._state.adding

        if is_new:
            if not self.delivered_at:
                self.delivered_at = timezone.now()
            if not self.current_location and self.customerid and self.customerid.address:
                self.current_location = self.customerid.address

        if self.pk:
            try:
                old = Shipment.objects.get(pk=self.pk)
                old_status = old.delivery_status
            except Shipment.DoesNotExist:
                old_status = None
        else:
            old_status = None

        status_changed = self.delivery_status != old_status
        if status_changed or is_new:
            self.status_updated_at = timezone.now()
            if str(self.delivery_status).lower() == 'delivered':
                self.delivered_at = timezone.now()

        super().save(*args, **kwargs)

        if status_changed or is_new:
            ShipmentStatusHistory.objects.create(
                shipment=self,
                status=str(self.delivery_status or "PENDING").upper(),
                timestamp=self.status_updated_at,
            )



class Invoice(models.Model):
    STATUS_CHOICES = (
        ('PAID', 'Paid'),
        ('PENDING', 'Pending'),
        ('CANCELLED', 'Cancelled'),
    )
    user = models.ForeignKey(sign, on_delete=models.CASCADE, null=True, blank=True)
    booking = models.ForeignKey(Shipment, on_delete=models.CASCADE, null=True, blank=True)
    invoice_id = models.CharField(max_length=30, unique=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    pdf = models.FileField(upload_to='static/invoices/', blank=True, null=True)

    def __str__(self):
        return self.invoice_id
    

class PaymentMethod(models.Model):
    METHOD_CHOICES = (
        ('UPI', 'UPI'),
        ('COD', 'Cash on Delivery'),
    )
    user = models.ForeignKey(sign, on_delete=models.CASCADE, null=True, blank=True)
    method_type = models.CharField(max_length=10, choices=METHOD_CHOICES)
    upi_id = models.CharField(max_length=50, blank=True, null=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.method_type == 'UPI':
            return f"UPI {self.upi_id}"
        return "COD"
    

class ReviewUser(models.Model):
    booking = models.ForeignKey(Shipment, on_delete=models.CASCADE, null=True, blank=True)
    star = models.IntegerField(null=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.booking.trackingId if self.booking else self.id)