from django.db import models

# Create your models here.


class contactus(models.Model):
    name = models.CharField(max_length=100, null=True)
    phone = models.IntegerField(null=True)
    email = models.EmailField(max_length=100, null=True)
    details = models.TextField(null=True)
    address = models.TextField(null=True)
    date = models.DateTimeField(null=True)
    def __str__(self):
        return self.email

class sign(models.Model):
    name = models.CharField(max_length=100, null=True)
    email = models.EmailField(max_length=100, null=True)
    phone = models.IntegerField(null=True)
    address = models.TextField(null=True)
    image = models.ImageField(blank=True, null=True, upload_to="static/userImage/")
    mpass = models.CharField(max_length=100, null=True)
    cpass = models.CharField(max_length=100, null=True)
    date = models.DateTimeField(null=True)
    def __str__(self):
        return self.email

