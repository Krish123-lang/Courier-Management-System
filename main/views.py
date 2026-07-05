from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import *
from datetime import datetime
import re

# Create your views here.


def _is_strong_password(password: str) -> bool:
    return len(password) >= 8 and re.search(r"[A-Z]", password) and re.search(r"[a-z]", password) and re.search(r"\d", password)


def _build_image_url(image_value) -> str:
    if not image_value:
        return ""
    image_value = str(image_value)
    if image_value.startswith(("http://", "https://", "/")):
        return image_value
    if image_value.startswith("static/"):
        return f"/{image_value}"
    return f"/static/{image_value}"


def home(request):
    return render(request, "home.html")


def contact(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        mobile = (request.POST.get("num") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        address = (request.POST.get("address") or "").strip()
        query = (request.POST.get("que") or "").strip()

        if not all([name, mobile, email, address, query]):
            messages.error(request, "Please fill in all contact fields before submitting.")
            return redirect("contact")

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please provide a valid email address.")
            return redirect("contact")

        if len(mobile) < 10 or not mobile.isdigit():
            messages.error(request, "Please provide a valid phone number.")
            return redirect("contact")

        contactus(name=name, phone=mobile, email=email, address=address, details=query, date=datetime.now()).save()
        messages.success(request, "Your query has been sent. We will respond within two working days.")
        return redirect("contact")
    return render(request, "contact.html")


def signup(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        number = (request.POST.get("num") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        address = (request.POST.get("address") or "").strip()
        image = request.FILES.get("image")
        mpass = request.POST.get("pass") or ""
        cpass = request.POST.get("cpass") or ""

        if not all([name, number, email, address, mpass, cpass]):
            messages.error(request, "Please fill in all required fields.")
            return redirect("signup")

        if len(number) < 10 or not number.isdigit():
            messages.error(request, "Please enter a valid phone number.")
            return redirect("signup")

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return redirect("signup")

        if sign.objects.filter(email=email).exists():
            messages.error(request, "The email is already registered.")
            return redirect("signup")
        if sign.objects.filter(phone=number).exists():
            messages.error(request, "The mobile number is already registered.")
            return redirect("signup")
        if mpass != cpass:
            messages.error(request, "Your password and confirm password do not match.")
            return redirect("signup")
        if not _is_strong_password(mpass):
            messages.error(request, "Password must be at least 8 characters and include uppercase, lowercase, and a number.")
            return redirect("signup")

        hashed_password = make_password(mpass)
        sign(name=name, email=email, phone=number, image=image, address=address, mpass=hashed_password, cpass=hashed_password, date=datetime.now()).save()
        messages.success(request, "Your account was created successfully. You can log in now.")
        return redirect("login")

    return render(request, "signup.html")


def login(request):
    if request.session.get("email"):
        return redirect("dashboard")

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("pass") or ""

        if not email or not password:
            messages.error(request, "Please enter both email and password.")
            return redirect("login")

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return redirect("login")

        user = sign.objects.filter(email=email).first()
        password_matches = bool(user and (check_password(password, user.mpass) or user.mpass == password))
        if user and password_matches:
            if user.mpass == password:
                user.mpass = make_password(password)
                user.cpass = make_password(password)
                user.save(update_fields=["mpass", "cpass"])
            request.session["name"] = str(user.name)
            request.session["email"] = str(user.email)
            request.session["number"] = str(user.phone)
            request.session["address"] = str(user.address or "")
            request.session["image"] = _build_image_url(user.image)
            return redirect("dashboard")
        if sign.objects.filter(email=email).exists():
            messages.error(request, "Your email or password is incorrect.")
            return redirect("login")
        messages.error(request, "Your email is not registered. Please sign up first.")
        return redirect("signup")

    return render(request, "login.html")


def dom(request):
    return render(request, "domestic.html")


def vas(request):
    return render(request, "valueAdded.html")


def about(request):
    return render(request, "about.html")


def team(request):
    return render(request, "team.html")