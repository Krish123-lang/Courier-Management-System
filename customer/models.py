from django.db import models
from django.utils import timezone
from main.models import *
import string, random

# Create your models here.


def generate_trackingId():
    ch = string.ascii_uppercase + string.digits
    return "".join(random.choice(ch) for _ in range(10))

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
    current_location = models.CharField(max_length=50, null=True)
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

    def save(self, *args, **kwargs):
        # Update status_updated_at whenever status changes
        if self.pk:
            try:
                old = Shipment.objects.get(pk=self.pk)
                old_status = old.delivery_status
            except Shipment.DoesNotExist:
                old_status = None
        else:
            old_status = None

        if self.delivery_status != old_status:
            self.status_updated_at = timezone.now()
            if str(self.delivery_status).lower() == 'DELIVERED':
                self.delivered_at = timezone.now()

        super().save(*args, **kwargs)



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