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

def book(request):
    SN = request.session.get("name")
    if(request.method == "POST"):
        user_email = request.session.get("email")
        userObj = sign.objects.get(email=user_email)
        SA = request.POST["senderAddress"]
        SP = request.POST["senderPhone"]
        RN = request.POST["receiverName"]
        RA = request.POST["receiverAddress"]
        RP = request.POST["receiverPhone"]
        Weight = request.POST["weight"]
        Service = request.POST["serviceType"]
        Rs = request.POST["money"]
        Shipment.objects.create(
            customerid=userObj,
            sender_name=SN,
            pickupAddress=SA,
            senderNumber=SP,
            recipientName=RN,
            recipientAddress=RA,
            recipientNumber=RP,
            package_description=Weight,
            service_type=Service,
            shipping_cost=Rs,
        )
        messages.success(request, "Process Of Shipment is completed. We will Notify you about your rider soon on your mobile number " + SP + " or registered mobile number and registered gmail")
        return redirect('book')
    return render(request, "booking.html", {"SN" : SN})

def hist(request):
    if(request.session.get("email")):
        user_email = request.session.get("email")
        user_obj = sign.objects.get(email=user_email)
        user_shipments = Shipment.objects.filter(customerid=user_obj)
        active_shipments = user_shipments.exclude(delivery_status='DELIVERED').order_by('-created_at')
        delivered_shipments = user_shipments.filter(delivery_status='DELIVERED').order_by('-delivered_at')
        data = {
            "active_shipments" : active_shipments,
            "delivered_shipments" : delivered_shipments,
        }
        return render(request, "history.html", data)
    return render(request, "history.html")

def review(request):
    tid = request.GET.get("id")  #Fetching id from url
    shipment_obj = get_object_or_404(Shipment, trackingId=tid)
    if(request.method == "POST"):
        R = request.POST.get("rev")
        ReviewUser(booking=shipment_obj, star=R, date=datetime.now()).save()
        messages.success(request, "Your Review has submitted.")
        return redirect('review')
    return render(request, "review.html")


def bill(request):
    user_email = request.session.get("email")
    if not user_email:
        messages.error(request, "You have to login first.")
        return redirect("signup")   # or your login/signup url name
    try:
        user_obj = sign.objects.get(email=user_email)
    except sign.DoesNotExist:
        messages.error(request, "User not found. Please login again.")
        return redirect("signup")

    # all invoices for this user
    invoices = Invoice.objects.filter(user=user_obj).order_by("-created_at")
    payment_methods = PaymentMethod.objects.filter(user=user_obj).order_by("-created_at")
    context = {
        "invoices": invoices,
        "payment_methods": payment_methods,
    }
    return render(request, "bill.html", context)

def profile(request):
    name = request.session.get("name")
    email = request.session.get("email")
    number = request.session.get("number")
    address = request.session.get("address")
    image = request.session.get("image")
    data = {
        'name' : name,
        'email' : email,
        'number' : number,
        'address' : address,
        'image' : image,
    }
    return render(request, "profile.html", data)

def helpCenter(request):
    return render(request, "help.html")
