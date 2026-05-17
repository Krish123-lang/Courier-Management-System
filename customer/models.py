from django.db import models
from django.utils import timezone
from main.models import *
import string, random

# Create your models here.


def generate_trackingId():
    ch = string.ascii_uppercase + string.digits
    return "".join(random.choice(ch) for _ in range(10))

class booking(models.Model):
    status_choices = (
        ('Pending', 'Pending'),
        ('out', 'out'),
        ('hub', 'hub'),
        ('depart', 'depart'),
        ('delivered', 'delivered'),
        ('cancelled', 'cancelled'),
    )
    userid = models.ForeignKey(sign, on_delete=models.CASCADE, null=True, blank=True)
    trackingId = models.CharField(max_length=20, default = generate_trackingId, unique=True, null=True)
    status = models.CharField(max_length=50, default="Pending", choices=status_choices, null=True)
    delivered_date = models.DateTimeField(null=True, blank=True)
    reached_status_date = models.DateTimeField(null=True, blank=True)
    delivery_place_status = models.CharField(max_length=50, null=True)
    name = models.CharField(max_length=100, null=True)
    pickupAddress = models.TextField(null=True)
    senderNumber = models.IntegerField(null=True)
    recipientName = models.CharField(max_length=100, null=True)
    recipientAddress = models.TextField(null=True)
    recipientNumber = models.IntegerField(null=True)
    package = models.CharField(max_length=100, null=True)
    service = models.CharField(max_length=100, null=True)
    date = models.DateTimeField(auto_now_add=True)
    rs = models.CharField(max_length=10, null=True)

    def __str__(self):
        return str(self.trackingId or self.id)

    def save(self, *args, **kwargs):
        # Update reached_status_date whenever status changes
        if self.pk:
            try:
                old = booking.objects.get(pk=self.pk)
                old_status = old.status
            except booking.DoesNotExist:
                old_status = None
        else:
            old_status = None

        if self.status != old_status:
            self.reached_status_date = timezone.now()
            if str(self.status).lower() == 'delivered':
                self.delivered_date = timezone.now()

        super().save(*args, **kwargs)

