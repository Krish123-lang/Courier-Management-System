from django.db import models
from django.utils import timezone
from main.models import sign

# Create your models here.


def generate_tracking_number():
    prefix = "CMS"
    year = timezone.now().year
    last_shipment = Shipment.objects.filter(trackingId__startswith=f"{prefix}-{year}-").order_by("trackingId").last()
    if last_shipment and last_shipment.trackingId:
        try:
            seq = int(last_shipment.trackingId.rsplit("-", 1)[-1])
        except ValueError:
            seq = 0
    else:
        seq = 0
    return f"{prefix}-{year}-{seq+1:06d}"


def generate_trackingId():
    return generate_tracking_number()

class Shipment(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_ASSIGNED = "ASSIGNED"
    STATUS_PICKED_UP = "PICKED_UP"
    STATUS_AT_ORIGIN_HUB = "AT_ORIGIN_HUB"
    STATUS_IN_TRANSIT = "IN_TRANSIT"
    STATUS_AT_DESTINATION_HUB = "AT_DESTINATION_HUB"
    STATUS_OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    STATUS_DELIVERED = "DELIVERED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_RETURNED = "RETURNED"
    STATUS_DELIVERY_FAILED = "DELIVERY_FAILED"

    WORKFLOW = [
        STATUS_PENDING,
        STATUS_APPROVED,
        STATUS_ASSIGNED,
        STATUS_PICKED_UP,
        STATUS_AT_ORIGIN_HUB,
        STATUS_IN_TRANSIT,
        STATUS_AT_DESTINATION_HUB,
        STATUS_OUT_FOR_DELIVERY,
        STATUS_DELIVERED,
    ]

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_ASSIGNED, "Assigned"),
        (STATUS_PICKED_UP, "Picked Up"),
        (STATUS_AT_ORIGIN_HUB, "At Origin Hub"),
        (STATUS_IN_TRANSIT, "In Transit"),
        (STATUS_AT_DESTINATION_HUB, "At Destination Hub"),
        (STATUS_OUT_FOR_DELIVERY, "Out For Delivery"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_RETURNED, "Returned"),
        (STATUS_DELIVERY_FAILED, "Delivery Failed"),
    )

    LEGACY_STATUS_MAP = {
        'Pending': STATUS_PENDING,
        'pending': STATUS_PENDING,
        'AT_HUB': STATUS_AT_ORIGIN_HUB,
        'At Hub': STATUS_AT_ORIGIN_HUB,
        'DEPARTED': STATUS_IN_TRANSIT,
        'Departed': STATUS_IN_TRANSIT,
    }

    customerid = models.ForeignKey(sign, on_delete=models.CASCADE, null=True, blank=True)
    trackingId = models.CharField(max_length=20, default=generate_trackingId, unique=True, null=True)
    delivery_status = models.CharField(max_length=50, default=STATUS_PENDING, choices=STATUS_CHOICES)
    delivered_at = models.DateTimeField(null=True, blank=True)
    status_updated_at = models.DateTimeField(null=True, blank=True)
    current_location = models.CharField(max_length=100, null=True, blank=True)
    sender_name = models.CharField(max_length=100, null=True, blank=True)
    pickupAddress = models.TextField(null=True, blank=True)
    senderNumber = models.CharField(max_length=15, null=True, blank=True)
    recipientName = models.CharField(max_length=100, null=True, blank=True)
    recipientAddress = models.TextField(null=True, blank=True)
    recipientNumber = models.CharField(max_length=15, null=True, blank=True)
    package_description = models.CharField(max_length=100, null=True, blank=True)
    service_type = models.CharField(max_length=100, null=True, blank=True)
    package_type = models.CharField(max_length=50, null=True, blank=True)
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    length = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    width = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    declared_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    fragile = models.BooleanField(default=False)
    insurance = models.BooleanField(default=False)
    base_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    weight_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return str(self.trackingId or self.id)

    @classmethod
    def normalize_status(cls, status):
        if not status:
            return cls.STATUS_PENDING
        return cls.LEGACY_STATUS_MAP.get(status, status)

    def can_transition(self, new_status: str) -> bool:
        new_status = self.normalize_status(new_status)
        current_status = self.normalize_status(self.delivery_status)

        if current_status == new_status:
            return True

        if current_status in {
            self.STATUS_DELIVERED,
            self.STATUS_CANCELLED,
            self.STATUS_RETURNED,
            self.STATUS_DELIVERY_FAILED,
        }:
            return False

        if new_status in {
            self.STATUS_CANCELLED,
            self.STATUS_RETURNED,
            self.STATUS_DELIVERY_FAILED,
        }:
            return True

        if current_status not in self.WORKFLOW or new_status not in self.WORKFLOW:
            return False

        current_index = self.WORKFLOW.index(current_status)
        return current_index + 1 < len(self.WORKFLOW) and self.WORKFLOW[current_index + 1] == new_status

    def calculate_shipping_cost(self):
        self.base_charge = 50
        self.weight_charge = 0
        self.service_charge = 0

        if self.weight and self.weight > 1:
            self.weight_charge = round((self.weight - 1) * 20, 2)

        service_rates = {
            'Economy': 20,
            'Standard': 40,
            'Express': 80,
            'Same Day': 150,
        }
        self.service_charge = service_rates.get(self.service_type, 0)
        self.shipping_cost = self.base_charge + self.weight_charge + self.service_charge

        if self.insurance and self.declared_value:
            self.shipping_cost += round(self.declared_value * 0.01, 2)

        self.total_cost = self.shipping_cost

    def _create_tracking_record(self, old_status: str = None):
        new_status = self.normalize_status(self.delivery_status)
        old_status = self.normalize_status(old_status) if old_status is not None else None
        if old_status is not None and old_status == new_status:
            return
        ShipmentTracking.objects.create(
            shipment=self,
            status=new_status,
            updated_by=self.customerid,
            location=self.current_location,
            remarks="Status updated",
        )

    def save(self, *args, **kwargs):
        self.delivery_status = self.normalize_status(self.delivery_status)
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

        self.calculate_shipping_cost()

        if self.delivery_status != old_status:
            if old_status is not None and not self.can_transition(self.delivery_status):
                raise ValueError(f"Invalid shipment status transition from {old_status} to {self.delivery_status}.")
            self.status_updated_at = timezone.now()
            if self.delivery_status == self.STATUS_DELIVERED:
                self.delivered_at = timezone.now()

        super().save(*args, **kwargs)

        self._create_tracking_record(old_status)


class ShipmentTracking(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='tracking_history')
    status = models.CharField(max_length=50, choices=Shipment.STATUS_CHOICES)
    updated_by = models.ForeignKey(sign, on_delete=models.SET_NULL, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.shipment.trackingId} - {self.status}"


class DeliveryAssignment(models.Model):
    STATUS_CHOICES = (
        ('ASSIGNED', 'Assigned'),
        ('ACCEPTED', 'Accepted'),
        ('DECLINED', 'Declined'),
    )

    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='assignments')
    delivery_staff = models.ForeignKey(sign, on_delete=models.CASCADE, related_name='delivery_assignments')
    assigned_by = models.ForeignKey(sign, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_shipments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ASSIGNED')

    def __str__(self):
        return f"{self.shipment.trackingId} assigned to {self.delivery_staff.email}"


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