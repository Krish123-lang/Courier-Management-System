
# class Invoice(models.Model):
#     STATUS_CHOICES = (
#         ('PAID', 'Paid'),
#         ('PENDING', 'Pending'),
#         ('CANCELLED', 'Cancelled'),
#     )
#     user = models.ForeignKey(sign, on_delete=models.CASCADE, null=True, blank=True)        
#     booking = models.ForeignKey(booking, on_delete=models.CASCADE, null=True, blank=True)
#     invoice_id = models.CharField(max_length=30, unique=True)
#     amount = models.DecimalField(max_digits=8, decimal_places=2)
#     status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
#     created_at = models.DateTimeField(auto_now_add=True)
#     pdf = models.FileField(upload_to='static/invoices/', blank=True, null=True)

#     def __str__(self):
#         return self.invoice_id
    

# class PaymentMethod(models.Model):
#     METHOD_CHOICES = (
#         ('UPI', 'UPI'),
#         ('COD', 'Cash on Delivery'),
#     )
#     user = models.ForeignKey(sign, on_delete=models.CASCADE, null=True, blank=True)
#     method_type = models.CharField(max_length=10, choices=METHOD_CHOICES)
#     upi_id = models.CharField(max_length=50, blank=True, null=True)
#     is_default = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def _str_(self):
#         if self.method_type == 'UPI':
#             return f"UPI {self.upi_id}"
#         return "COD"
    

# class ReviewUser(models.Model):
#     booking = models.ForeignKey(booking, on_delete=models.CASCADE, null=True, blank=True)
#     star = models.IntegerField(null=True)
#     date = models.DateTimeField(auto_now_add=True)

#     def _str_(self):
#         return self.booking.trackingId