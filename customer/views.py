from urllib import request
from django.shortcuts import render, redirect
from datetime import datetime
from django.contrib import messages
from .models import *
from main.models import *
from django.shortcuts import get_object_or_404

# Create your views here.

def dash(request):
    abc = request.session.get("email")
    userObj = sign.objects.get(email=abc)
    total_shipments = Shipment.objects.filter(customerid = userObj).count()
    in_transit = Shipment.objects.filter(customerid = userObj, delivery_status='AT_HUB').count()
    delivered = Shipment.objects.filter(customerid = userObj, delivery_status='DELIVERED').count()
    cancelled = Shipment.objects.filter(customerid = userObj, delivery_status='CANCELLED').count()
    recent_shipments = Shipment.objects.filter(customerid = userObj).order_by('-created_at')[:5]
    context = {
        'total_shipments': total_shipments,
        'in_transit': in_transit,
        'delivered': delivered,
        'cancelled': cancelled,
        'customerid' : abc,
        'recent_shipments': recent_shipments,
    }
    return render(request, 'dashboard.html', context)


def track(request):
    tid = request.GET.get("id")
    if(request.session.get("email")):
        user_bookings = Shipment.objects.filter(trackingId = tid)
        active_shipments = user_bookings.exclude(delivery_status='delivered').order_by('-created_at')
        data = {
            "active_shipments" : active_shipments,
        }
        return render(request, "track.html", data)
    return render(request, "track.html")


def signout(request):
    user = request.session.get("email")
    if user : 
        del request.session["name"]
        del request.session["email"]
        del request.session["number"]
        request.session.flush()
        return redirect("home")
    return render(request, "signup.html")