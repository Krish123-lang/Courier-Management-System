from django.shortcuts import render, redirect
from datetime import datetime, timedelta
from decimal import Decimal
from django.contrib import messages
from django.core.files.base import ContentFile
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import *
from main.models import *
from django.shortcuts import get_object_or_404
from django.conf import settings
import base64
import json
import os
import re
import urllib.request
import urllib.parse


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


def _paypal_get_access_token():
    client_id = getattr(settings, "PAYPAL_CLIENT_ID", "") or os.getenv("PAYPAL_CLIENT_ID", "")
    client_secret = getattr(settings, "PAYPAL_CLIENT_SECRET", "") or os.getenv("PAYPAL_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        raise RuntimeError("PayPal sandbox credentials are not configured.")

    mode = getattr(settings, "PAYPAL_MODE", "sandbox") or os.getenv("PAYPAL_MODE", "sandbox")
    api_base = "https://api-m.sandbox.paypal.com" if str(mode).lower() == "sandbox" else "https://api-m.paypal.com"
    url = f"{api_base}/v1/oauth2/token"
    payload = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode("utf-8")
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data.get("access_token")


def _paypal_create_order_request(invoice):
    token = _paypal_get_access_token()
    if not token:
        raise RuntimeError("PayPal access token could not be generated.")

    mode = getattr(settings, "PAYPAL_MODE", "sandbox") or os.getenv("PAYPAL_MODE", "sandbox")
    api_base = "https://api-m.sandbox.paypal.com" if str(mode).lower() == "sandbox" else "https://api-m.paypal.com"
    url = f"{api_base}/v2/checkout/orders"
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": f"invoice-{invoice.invoice_id}",
                "description": f"Courier service invoice {invoice.invoice_id}",
                "amount": {
                    "currency_code": getattr(settings, "PAYPAL_CURRENCY", "USD") or os.getenv("PAYPAL_CURRENCY", "USD"),
                    "value": f"{invoice.amount:.2f}",
                },
            }
        ],
        "application_context": {
            "return_url": f"{getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}/user/paypal/return/?invoice_id={invoice.id}",
            "cancel_url": f"{getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}/user/paypal/cancel/",
        },
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        data = json.loads(response.read().decode("utf-8"))
    approve_link = next((link.get("href") for link in data.get("links", []) if link.get("rel") == "approve"), None)
    return data, approve_link


def _paypal_capture_order_request(order_id):
    token = _paypal_get_access_token()
    if not token:
        raise RuntimeError("PayPal access token could not be generated.")

    mode = getattr(settings, "PAYPAL_MODE", "sandbox") or os.getenv("PAYPAL_MODE", "sandbox")
    api_base = "https://api-m.sandbox.paypal.com" if str(mode).lower() == "sandbox" else "https://api-m.paypal.com"
    url = f"{api_base}/v2/checkout/orders/{order_id}/capture"
    request = urllib.request.Request(
        url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data.get("status") == "COMPLETED"


def _generate_invoice_pdf(invoice):
    if not invoice:
        return None

    invoice_date = invoice.created_at.strftime('%d %b %Y') if invoice.created_at else 'N/A'
    due_date = (invoice.created_at + timedelta(days=7)).strftime('%d %b %Y') if invoice.created_at else 'N/A'

    customer_name = invoice.user.name if invoice.user else 'Guest Customer'
    customer_email = invoice.user.email if invoice.user else 'N/A'
    booking_ref = invoice.booking.trackingId if invoice.booking else 'N/A'

    lines = [
        "COURIER HUB LOGISTICS",
        "Invoice Receipt",
        "",
        f"Invoice ID: {invoice.invoice_id}",
        f"Date: {invoice_date}",
        f"Due Date: {due_date}",
        f"Status: {invoice.status}",
        "",
        "Bill To",
        customer_name,
        customer_email,
        "",
        "Service Summary",
        f"Shipment Reference: {booking_ref}",
        f"Amount Due: {invoice.amount:.2f}",
        f"Payment Method: PayPal Sandbox",
        "",
        "Thank you for choosing Courier Hub Logistics.",
        "This is a payment receipt for your courier service invoice.",
    ]

    def escape_pdf_text(value):
        return str(value).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    content_parts = []
    y_position = 760

    content_parts.append("BT /F1 16 Tf 72 760 Td (COURIER HUB LOGISTICS) Tj ET")
    content_parts.append("BT /F1 10 Tf 72 740 Td (Invoice Receipt) Tj ET")
    content_parts.append("BT /F1 10 Tf 72 720 Td (========================================) Tj ET")

    y_position = 690
    for line in lines[3:]:
        content_parts.append(f"BT /F1 10 Tf 72 {y_position} Td ({escape_pdf_text(line)}) Tj ET")
        y_position -= 14

    content_parts.append("BT /F1 10 Tf 72 360 Td (Payment Status: Paid) Tj ET")
    content_parts.append("BT /F1 10 Tf 72 342 Td (Amount Received: 0.00) Tj ET")
    content_parts.append("BT /F1 10 Tf 72 324 Td (Transaction ID: PAYPAL-SANDBOX) Tj ET")
    content_parts.append("BT /F1 10 Tf 72 90 Td (Generated by Courier Hub Logistics - Thank you) Tj ET")

    content_stream = "\n".join(content_parts)
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        "<< /Length 0 >>\nstream\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    objects[3] = f"<< /Length {len(content_stream.encode('latin-1'))} >>\nstream\n{content_stream}\nendstream"

    pdf_parts = ["%PDF-1.4"]
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len("\n".join(pdf_parts).encode("latin-1")))
        pdf_parts.append(f"{index} 0 obj")
        pdf_parts.append(obj)
        pdf_parts.append("endobj")

    xref_position = len("\n".join(pdf_parts).encode("latin-1"))
    pdf_parts.append("xref")
    pdf_parts.append(f"0 {len(objects) + 1}")
    pdf_parts.append("0000000000 65535 f ")
    for offset in offsets[1:]:
        pdf_parts.append(f"{offset:010d} 00000 n ")

    pdf_parts.append("trailer")
    pdf_parts.append(f"<< /Size {len(objects) + 1} /Root 1 0 R >>")
    pdf_parts.append("startxref")
    pdf_parts.append(str(xref_position))
    pdf_parts.append("%%EOF")

    return "\n".join(pdf_parts).encode("latin-1")

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

    dashboard_shipments = Shipment.objects.filter(customerid=user_obj).order_by("-created_at")
    recent_shipments = list(dashboard_shipments[:5])

    in_transit = 0
    delivered = 0
    cancelled = 0
    for shipment in dashboard_shipments:
        status = Shipment.normalize_delivery_status(getattr(shipment, "delivery_status", None))
        if status in {"AT_HUB", "OUT_FOR_DELIVERY", "DEPARTED"}:
            in_transit += 1
        elif status == "DELIVERED":
            delivered += 1
        elif status == "CANCELLED":
            cancelled += 1

    context = {
        "total_shipments": dashboard_shipments.count(),
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
    active_shipments = Shipment.objects.filter(trackingId=tid).order_by("-created_at") if tid else Shipment.objects.none()
    data = {"active_shipments": active_shipments}
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

        shipment_obj = Shipment.objects.create(
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
        invoice_id = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}-{shipment_obj.id}"
        Invoice.objects.create(
            user=user_obj,
            booking=shipment_obj,
            invoice_id=invoice_id,
            amount=Decimal(str(amount)),
            status="PENDING",
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
    paypal_ready = bool(getattr(settings, "PAYPAL_CLIENT_ID", "") or os.getenv("PAYPAL_CLIENT_ID", "")) and bool(getattr(settings, "PAYPAL_CLIENT_SECRET", "") or os.getenv("PAYPAL_CLIENT_SECRET", ""))
    context = {"invoices": invoices, "payment_methods": payment_methods, "paypal_ready": paypal_ready}
    return render(request, "bill.html", context)


def paypal_create_order(request, invoice_id):
    if not request.session.get("email"):
        messages.error(request, "You have to login first.")
        return redirect("login")

    user_obj = sign.objects.filter(email=request.session.get("email")).first()
    if not user_obj:
        messages.error(request, "User not found. Please login again.")
        return redirect("login")

    invoice = get_object_or_404(Invoice, id=invoice_id, user=user_obj)
    if invoice.status == "PAID":
        messages.info(request, "This invoice is already paid.")
        return redirect("bill")

    try:
        _, approve_link = _paypal_create_order_request(invoice)
    except Exception as exc:
        messages.error(request, f"Unable to start PayPal checkout: {exc}")
        return redirect("bill")

    if not approve_link:
        messages.error(request, "PayPal did not return an approval URL.")
        return redirect("bill")

    return redirect(approve_link)


def paypal_return(request):
    invoice_id = request.GET.get("invoice_id")
    order_id = request.GET.get("token") or request.GET.get("orderId")
    payer_id = request.GET.get("PayerID")

    if not invoice_id or not order_id or not payer_id:
        messages.error(request, "PayPal payment was cancelled or incomplete.")
        return redirect("bill")

    invoice = get_object_or_404(Invoice, id=invoice_id)
    if invoice.user:
        request.session["email"] = invoice.user.email
        request.session["name"] = str(invoice.user.name)
        request.session["number"] = str(invoice.user.phone)
        request.session["address"] = str(invoice.user.address or "")
        request.session["image"] = _build_image_url(invoice.user.image)

    try:
        captured = _paypal_capture_order_request(order_id)
    except Exception as exc:
        messages.error(request, f"PayPal capture failed: {exc}")
        return redirect("bill")

    if captured:
        invoice.status = "PAID"
        invoice.save(update_fields=["status"])
        if not invoice.pdf:
            pdf_bytes = _generate_invoice_pdf(invoice)
            if pdf_bytes:
                file_name = f"{invoice.invoice_id.replace(' ', '_')}.pdf"
                invoice.pdf.save(file_name, ContentFile(pdf_bytes), save=False)
                invoice.save(update_fields=["pdf"])
        messages.success(request, f"Invoice {invoice.invoice_id} was paid successfully.")
    else:
        messages.error(request, "PayPal payment could not be completed.")
    return redirect("bill")


def paypal_cancel(request):
    messages.info(request, "PayPal payment was cancelled.")
    return redirect("bill")


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


def helpCenter(request):
    return render(request, "help.html")
