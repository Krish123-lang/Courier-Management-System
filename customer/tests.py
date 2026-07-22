from unittest.mock import patch
from django.utils import timezone
from django.test import TestCase
from django.contrib.auth.hashers import check_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from main.models import sign
from .models import ReviewUser, Shipment, ShipmentStatusHistory, Invoice


class ShipmentAndReviewModelTests(TestCase):
    def test_paypal_create_order_redirects_to_approval_url(self):
        user = sign.objects.create(
            name="Paypal User",
            email="paypal@example.com",
            phone=5555555555,
            address="Paypal address",
            mpass="Password123",
            cpass="Password123",
            date=timezone.now(),
        )
        invoice = Invoice.objects.create(
            user=user,
            invoice_id="INV-PP-001",
            amount="25.50",
            status="PENDING",
        )
        session = self.client.session
        session["email"] = user.email
        session["name"] = user.name
        session["number"] = str(user.phone)
        session["address"] = user.address
        session.save()

        with patch("customer.views._paypal_create_order_request", return_value=(
            {"id": "ORDER-123", "links": [{"rel": "approve", "href": "https://www.sandbox.paypal.com/checkoutnow?token=ORDER-123"}]},
            "https://www.sandbox.paypal.com/checkoutnow?token=ORDER-123",
        )):
            response = self.client.post(reverse("paypal_create_order", args=[invoice.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://www.sandbox.paypal.com/checkoutnow?token=ORDER-123")

    def test_paypal_return_marks_invoice_paid(self):
        user = sign.objects.create(
            name="Paypal Return User",
            email="paypalreturn@example.com",
            phone=6666666666,
            address="Paypal return address",
            mpass="Password123",
            cpass="Password123",
            date=timezone.now(),
        )
        invoice = Invoice.objects.create(
            user=user,
            invoice_id="INV-PP-002",
            amount="30.00",
            status="PENDING",
        )

        with patch("customer.views._paypal_capture_order_request", return_value=True):
            response = self.client.get(
                reverse("paypal_return"),
                {"invoice_id": invoice.id, "token": "TOKEN-123", "PayerID": "PAYER-123"},
            )

        invoice.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(invoice.status, "PAID")
        self.assertTrue(invoice.pdf)

    def test_passwords_are_hashed_on_create(self):
        user = sign.objects.create(
            name="Secure User",
            email="secure@example.com",
            phone=1234567890,
            address="Secure address",
            mpass="Password123",
            cpass="Password123",
            date=timezone.now(),
        )

        self.assertNotEqual(user.mpass, "Password123")
        self.assertNotEqual(user.cpass, "Password123")
        self.assertTrue(check_password("Password123", user.mpass))
        self.assertTrue(check_password("Password123", user.cpass))

    def test_create_shipment_and_review(self):
        user = sign.objects.create(
            name="Test User",
            email="test@example.com",
            phone=1234567890,
            address="Test address",
            mpass="password",
            cpass="password",
            date=timezone.now(),
        )
        shipment = Shipment.objects.create(
            customerid=user,
            sender_name="Test User",
            pickupAddress="Sender address",
            senderNumber="1234567890",
            recipientName="Recipient",
            recipientAddress="Recipient address",
            recipientNumber="9876543210",
            package_description="Box",
        )
        review = ReviewUser.objects.create(booking=shipment, star=5)

        self.assertEqual(review.booking, shipment)
        self.assertEqual(shipment.customerid, user)

    def test_profile_picture_can_be_updated_without_touching_other_fields(self):
        user = sign.objects.create(
            name="Profile User",
            email="profile@example.com",
            phone=1111111111,
            address="Old address",
            mpass="Password123",
            cpass="Password123",
            date=timezone.now(),
        )
        session = self.client.session
        session["email"] = user.email
        session["name"] = user.name
        session["number"] = str(user.phone)
        session["address"] = user.address
        session.save()

        image = SimpleUploadedFile("avatar.png", b"fake-image-bytes", content_type="image/png")
        response = self.client.post(
            reverse("profile"),
            {"profile_image": image},
            format="multipart",
        )

        user.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(user.image)
        self.assertIn("avatar", user.image.name)
        self.assertEqual(self.client.session["address"], "Old address")

    def test_new_shipments_get_default_delivery_time_and_location(self):
        user = sign.objects.create(
            name="Location User",
            email="location@example.com",
            phone=2222222222,
            address="Primary location",
            mpass="Password123",
            cpass="Password123",
            date=timezone.now(),
        )

        shipment = Shipment.objects.create(
            customerid=user,
            sender_name="Sender",
            pickupAddress="Pickup address",
            senderNumber="1234567890",
            recipientName="Recipient",
            recipientAddress="Recipient address",
            recipientNumber="9876543210",
            package_description="Box",
        )

        self.assertIsNotNone(shipment.delivered_at)
        self.assertEqual(shipment.current_location, "Primary location")

    def test_tracking_history_reflects_the_latest_delivery_status(self):
        user = sign.objects.create(
            name="Tracking User",
            email="tracking@example.com",
            phone=3333333333,
            address="Tracking address",
            mpass="Password123",
            cpass="Password123",
            date=timezone.now(),
        )

        shipment = Shipment.objects.create(
            customerid=user,
            sender_name="Sender",
            pickupAddress="Pickup address",
            senderNumber="1234567890",
            recipientName="Recipient",
            recipientAddress="Recipient address",
            recipientNumber="9876543210",
            package_description="Box",
            delivery_status="AT_HUB",
            current_location="Destination Hub",
        )

        history = shipment.get_tracking_history()
        titles = [step["title"] for step in history]

        self.assertEqual(titles, ["Order Placed", "Arrived at Destination Hub"])

        shipment.delivery_status = "DELIVERED"
        shipment.recipientAddress = "Recipient address"
        shipment.save(update_fields=["delivery_status", "recipientAddress"])

        history = shipment.get_tracking_history()
        titles = [step["title"] for step in history]

        self.assertEqual(
            titles,
            [
                "Order Placed",
                "Arrived at Destination Hub",
                "Out for Delivery",
                "Departed from Origin Hub",
                "Shipment Picked Up",
            ],
        )

    def test_dashboard_summary_counts_match_visible_recent_shipments(self):
        user = sign.objects.create(
            name="Dashboard User",
            email="dashboard@example.com",
            phone=4444444444,
            address="Dashboard address",
            mpass="Password123",
            cpass="Password123",
            date=timezone.now(),
        )

        Shipment.objects.create(
            customerid=user,
            sender_name="Sender",
            pickupAddress="Pickup address",
            senderNumber="1234567890",
            recipientName="Recipient",
            recipientAddress="Recipient address",
            recipientNumber="9876543210",
            package_description="Box",
            delivery_status="At hub",
        )
        Shipment.objects.create(
            customerid=user,
            sender_name="Sender",
            pickupAddress="Pickup address",
            senderNumber="1234567890",
            recipientName="Recipient",
            recipientAddress="Recipient address",
            recipientNumber="9876543210",
            package_description="Box",
            delivery_status="Delivered",
        )
        Shipment.objects.create(
            customerid=user,
            sender_name="Sender",
            pickupAddress="Pickup address",
            senderNumber="1234567890",
            recipientName="Recipient",
            recipientAddress="Recipient address",
            recipientNumber="9876543210",
            package_description="Box",
            delivery_status="Cancelled",
        )
        Shipment.objects.create(
            customerid=user,
            sender_name="Sender",
            pickupAddress="Pickup address",
            senderNumber="1234567890",
            recipientName="Recipient",
            recipientAddress="Recipient address",
            recipientNumber="9876543210",
            package_description="Box",
            delivery_status="DEPARTED",
        )
        Shipment.objects.create(
            customerid=user,
            sender_name="Sender",
            pickupAddress="Pickup address",
            senderNumber="1234567890",
            recipientName="Recipient",
            recipientAddress="Recipient address",
            recipientNumber="9876543210",
            package_description="Box",
            delivery_status="Delivered",
        )

        session = self.client.session
        session["email"] = user.email
        session["name"] = user.name
        session["number"] = str(user.phone)
        session["address"] = user.address
        session.save()

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_shipments"], 5)
        self.assertEqual(response.context["in_transit"], 2)
        self.assertEqual(response.context["delivered"], 2)
        self.assertEqual(response.context["cancelled"], 1)
