from django.utils import timezone
from django.test import TestCase
from main.models import sign
from .models import ReviewUser, Shipment


class ShipmentAndReviewModelTests(TestCase):
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
