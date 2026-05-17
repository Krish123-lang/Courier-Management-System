from django.contrib import admin
from .models import *

# Register your models here.

class bookingAdmin(admin.ModelAdmin):
    list_display = ("id", "trackingId", "name", "recipientName", "status")
admin.site.register(booking, bookingAdmin)


