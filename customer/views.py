import base64
import io
import re

import qrcode
from django.shortcuts import render, redirect
from django.urls import reverse
from datetime import datetime
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import *
from main.models import *
from django.shortcuts import get_object_or_404


def _build_image_url(image_value) -> str:
    if not image_value:
        return ""
    image_value = str(image_value)
    if image_value.startswith(("http://", "https://", "/")):
        return image_value
    if image_value.startswith("static/"):
        return f"/{image_value}"
    return f"/static/{image_value}"


def _is_valid_phone(phone: str) -> bool:
    return bool(re.fullmatch(r"\d{10}", phone))


def _build_qr_code_data_uri(data: str) -> str:
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{encoded}"


def _build_tracking_url(request, tracking_id: str) -> str:
    return request.build_absolute_uri(reverse("track") + f"?id={tracking_id}")

# Create your views here.

def dash(request):
    email = request.session.get("email")
    if not email:
        messages.error(request, "Please log in to access your dashboard.")
        return redirect("login")

    user_obj = sign.objects.filter(email=email).first()
    if not user_obj:
        messages.error(request, "Your session is invalid. Please log in again.")
        return redirect("login")

    total_shipments = Shipment.objects.filter(customerid=user_obj).count()
    in_transit = Shipment.objects.filter(customerid=user_obj, delivery_status__in=["AT_HUB", "OUT_FOR_DELIVERY", "DEPARTED"]).count()
    delivered = Shipment.objects.filter(customerid=user_obj, delivery_status="DELIVERED").count()
    cancelled = Shipment.objects.filter(customerid=user_obj, delivery_status="CANCELLED").count()
    recent_shipments = Shipment.objects.filter(customerid=user_obj).order_by("-created_at")[:5]
    context = {
        "total_shipments": total_shipments,
        "in_transit": in_transit,
        "delivered": delivered,
        "cancelled": cancelled,
        "customerid": email,
        "recent_shipments": recent_shipments,
    }
    return render(request, "dashboard.html", context)


def track(request):
    if not request.session.get("email"):
        messages.error(request, "Please log in to track your shipment.")
        return redirect("login")

    tid = request.GET.get("id")
    shipment = Shipment.objects.filter(trackingId=tid).order_by("-created_at").first() if tid else None
    tracking_history = shipment.tracking_history.all() if shipment else []
    qr_code = None
    if shipment and shipment.trackingId:
        qr_code = _build_qr_code_data_uri(_build_tracking_url(request, shipment.trackingId))
    data = {
        "shipment": shipment,
        "tracking_history": tracking_history,
        "qr_code": qr_code,
    }
    return render(request, "track.html", data)


def signout(request):
    if request.session.get("email"):
        request.session.flush()
        return redirect("home")
    return redirect("login")


def book(request):
    if not request.session.get("email"):
        messages.error(request, "Please log in to create a shipment.")
        return redirect("login")

    sender_name = request.session.get("name")
    sender_address_default = request.session.get("address") or ""
    sender_phone_default = request.session.get("number") or ""

    if request.method == "POST":
        user_email = request.session.get("email")
        user_obj = sign.objects.filter(email=user_email).first()
        if not user_obj:
            messages.error(request, "Your session is invalid. Please log in again.")
            return redirect("login")

        sender_address = (request.POST.get("senderAddress", "") or "").strip()
        sender_phone = (request.POST.get("senderPhone", "") or "").strip()
        receiver_name = (request.POST.get("receiverName", "") or "").strip()
        receiver_address = (request.POST.get("receiverAddress", "") or "").strip()
        receiver_phone = (request.POST.get("receiverPhone", "") or "").strip()
        weight = (request.POST.get("weight", "") or "").strip()
        service = (request.POST.get("serviceType", "") or "").strip()
        amount = (request.POST.get("money", "") or "").strip()

        if not all([sender_address, sender_phone, receiver_name, receiver_address, receiver_phone, weight, service, amount]):
            messages.error(request, "Please complete every required field to create a shipment.")
            return redirect("book")
        if not _is_valid_phone(sender_phone) or not _is_valid_phone(receiver_phone):
            messages.error(request, "Please enter valid 10-digit phone numbers for sender and receiver.")
            return redirect("book")
        if float(weight) <= 0 or float(amount) < 100:
            messages.error(request, "Weight must be greater than 0 and declared value must be at least 100.")
            return redirect("book")

        Shipment.objects.create(
            customerid=user_obj,
            sender_name=sender_name,
            pickupAddress=sender_address,
            senderNumber=sender_phone,
            recipientName=receiver_name,
            recipientAddress=receiver_address,
            recipientNumber=receiver_phone,
            package_description=weight,
            service_type=service,
            shipping_cost=amount,
        )
        messages.success(request, f"Your shipment request is in progress. We will contact you on {sender_phone} shortly.")
        return redirect("book")

    return render(request, "booking.html", {
        "SN": sender_name,
        "sender_address_default": sender_address_default,
        "sender_phone_default": sender_phone_default,
    })


def hist(request):
    if not request.session.get("email"):
        messages.error(request, "Please log in to view your shipment history.")
        return redirect("login")

    user_email = request.session.get("email")
    user_obj = sign.objects.filter(email=user_email).first()
    if not user_obj:
        messages.error(request, "Your session is invalid. Please log in again.")
        return redirect("login")

    user_shipments = Shipment.objects.filter(customerid=user_obj)
    active_shipments = user_shipments.exclude(delivery_status="DELIVERED").order_by("-created_at")
    delivered_shipments = user_shipments.filter(delivery_status="DELIVERED").order_by("-delivered_at")
    data = {"active_shipments": active_shipments, "delivered_shipments": delivered_shipments}
    return render(request, "history.html", data)


def review(request):
    if not request.session.get("email"):
        messages.error(request, "Please log in to submit a review.")
        return redirect("login")

    tid = request.GET.get("id")
    shipment_obj = get_object_or_404(Shipment, trackingId=tid) if tid else None
    if request.method == "POST":
        rating = request.POST.get("rev")
        if shipment_obj and rating:
            ReviewUser(booking=shipment_obj, star=rating, date=datetime.now()).save()
            messages.success(request, "Your review has been submitted.")
            return redirect("review")
        messages.error(request, "Please select a valid rating.")
        return redirect("review")

    return render(request, "review.html", {"shipment": shipment_obj})


def bill(request):
    user_email = request.session.get("email")
    if not user_email:
        messages.error(request, "You have to login first.")
        return redirect("login")

    user_obj = sign.objects.filter(email=user_email).first()
    if not user_obj:
        messages.error(request, "User not found. Please login again.")
        return redirect("login")

    invoices = Invoice.objects.filter(user=user_obj).order_by("-created_at")
    payment_methods = PaymentMethod.objects.filter(user=user_obj).order_by("-created_at")
    for inv in invoices:
        inv.qr_code = None
        if inv.booking and inv.booking.trackingId:
            inv.qr_code = _build_qr_code_data_uri(_build_tracking_url(request, inv.booking.trackingId))
    context = {"invoices": invoices, "payment_methods": payment_methods}
    return render(request, "bill.html", context)


def profile(request):
    if not request.session.get("email"):
        messages.error(request, "You have to login first.")
        return redirect("login")

    user_obj = sign.objects.filter(email=request.session.get("email")).first()
    if not user_obj:
        messages.error(request, "User not found. Please login again.")
        return redirect("login")

    if request.method == "POST":
        uploaded_image = request.FILES.get("profile_image")
        if uploaded_image:
            user_obj.image = uploaded_image
            user_obj.save(update_fields=["image"])
            request.session["image"] = _build_image_url(user_obj.image)
            messages.success(request, "Your profile picture has been updated successfully.")
        else:
            messages.error(request, "Please select a valid image file to upload.")
        return redirect("profile")

    name = request.session.get("name")
    email = request.session.get("email")
    number = request.session.get("number")
    address = request.session.get("address")
    image = request.session.get("image") or ""
    if not image and user_obj.image:
        image = _build_image_url(user_obj.image)
    data = {"name": name, "email": email, "number": number, "address": address, "image": image}
    return render(request, "profile.html", data)


def delivery_staff_actions(request):
    if not request.session.get("email"):
        messages.error(request, "Please log in to access delivery actions.")
        return redirect("login")

    user_email = request.session.get("email")
    user_obj = sign.objects.filter(email=user_email).first()
    if not user_obj:
        messages.error(request, "Your session is invalid. Please log in again.")
        return redirect("login")

    assignments = DeliveryAssignment.objects.filter(delivery_staff=user_obj).order_by("-assigned_at")
    shipment_ids = assignments.values_list("shipment_id", flat=True).distinct()
    shipments = Shipment.objects.filter(id__in=shipment_ids).order_by("-created_at")
    shipment_actions = []
    for shipment in shipments:
        shipment_actions.append({
            "shipment": shipment,
            "next_action": shipment.get_next_workflow_action(),
        })

    return render(request, "delivery_staff_actions.html", {
        "shipment_actions": shipment_actions,
        "assignments": assignments,
    })


def delivery_staff_action(request, shipment_id):
    if not request.session.get("email"):
        messages.error(request, "Please log in to access delivery actions.")
        return redirect("login")

    user_email = request.session.get("email")
    user_obj = sign.objects.filter(email=user_email).first()
    if not user_obj:
        messages.error(request, "Your session is invalid. Please log in again.")
        return redirect("login")

    shipment = get_object_or_404(Shipment, pk=shipment_id, assignments__delivery_staff=user_obj)
    next_action = shipment.get_next_workflow_action()
    if not next_action:
        messages.error(request, "This shipment has no next workflow action.")
        return redirect("delivery_staff_actions")

    if request.method == "POST":
        try:
            location = request.POST.get("location", shipment.current_location)
            shipment.perform_workflow_action(
                next_action["next_status"],
                updated_by=user_obj,
                location=location,
                remarks=next_action["label"],
            )
            messages.success(request, f"Shipment updated to {next_action['next_status']}.")
        except ValueError as exc:
            messages.error(request, str(exc))
        return redirect("delivery_staff_actions")

    return render(request, "delivery_staff_action.html", {
        "shipment": shipment,
        "next_action": next_action,
    })


def helpCenter(request):
    return render(request, "help.html")
