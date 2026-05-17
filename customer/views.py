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
    total_shipments = booking.objects.filter(userid = userObj).count()
    in_transit = booking.objects.filter(userid = userObj, status='hub').count()
    delivered = booking.objects.filter(userid = userObj, status='delivered').count()
    cancelled = booking.objects.filter(userid = userObj, status='cancelled').count()
    recent_shipments = booking.objects.filter(userid = userObj).order_by('-date')[:5]
    context = {
        'total_shipments': total_shipments,
        'in_transit': in_transit,
        'delivered': delivered,
        'cancelled': cancelled,
        'userid' : abc,
        'recent_shipments': recent_shipments,
    }
    return render(request, 'dashboard.html', context)


def track(request):
    tid = request.GET.get("id")
    if(request.session.get("email")):
        user_bookings = booking.objects.filter(trackingId = tid)
        active_shipments = user_bookings.exclude(status='Delivered').order_by('-date')
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