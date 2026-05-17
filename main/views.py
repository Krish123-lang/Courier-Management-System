from django.shortcuts import render, redirect
from django.contrib import messages
from .models import *
from datetime import datetime

# Create your views here.

def home(request):
    return render(request, "home.html")

def contact(request):
    if(request.method == "POST"):
        Name = request.POST.get('name')
        Mobile = request.POST.get('num')
        Email = request.POST.get('email')
        Address = request.POST.get('address')
        Query = request.POST.get('que')
        contactus(name = Name , phone = Mobile , email = Email , address = Address, details = Query, date = datetime.now()).save()
        messages.success(request, "Your Query has sent. We will respond in Two working days.")
        return redirect('contact')
    return render (request ,"contact.html")

def signup(request):
    if(request.method=="POST"):
        Name=request.POST.get('name')
        Number=request.POST.get('num')
        Email=request.POST.get('email')
        Address=request.POST.get('address')
        Image=request.FILES["image"]
        Mpass=request.POST.get('pass')
        Cpass=request.POST.get('cpass')

        if(sign.objects.filter(email=Email).exists()):
            messages.error(request, "The email is already registered.")
            return redirect('signup')
        elif(sign.objects.filter(phone=Number).exists()):
            messages.error(request, "The mobile number is already registered.")
            return redirect('signup')
        elif(Mpass!=Cpass):
            messages.error(request, "Your password and confirm passwords is not same.")
            return redirect('signup')
        else:
            sign(name = Name, email = Email, phone = Number, image = Image, address = Address, mpass = Mpass, cpass = Cpass, date = datetime.now()).save()
            messages.success(request, "Your account has created successfully. Now you can login.")
            return redirect('signup')
    
    return render(request,'signup.html')

def login(request):
    if(request.method == "POST"):
        Email = request.POST.get("email")
        Password = request.POST.get("pass")
        x = sign.objects.filter(email = Email, mpass = Password)
        if(x.count() == 1):
            #Sessions creation
            request.session["name"] = str(x[0].name)
            request.session["email"] = str(x[0].email)
            request.session["number"] = str(x[0].phone)
            request.session["address"] = str(x[0].address)
            request.session["image"] = str(x[0].image)
            return redirect('dashboard')
        elif(sign.objects.filter(email=Email).exists() == False):
            messages.error(request, "Your email is not registered. Please sign up first.")
            return redirect('signup')
        else:
            messages.error(request, "Your email or password is incorrect.")
            return redirect('login')
    return render(request, "login.html")

def dom(request):
    return render(request,"domestic.html")

def vas(request):
    return render(request,"valueAdded.html")

def about(request):
    return render(request,"about.html")

def team(request):
    return render(request,"team.html")