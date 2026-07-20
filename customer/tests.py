from django.utils import timezone
from django.test import TestCase
from django.contrib.auth.hashers import check_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from main.models import sign
from .models import ReviewUser, Shipment, ShipmentStatusHistory


class ShipmentAndReviewModelTests(TestCase):
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
