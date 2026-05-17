# def book(request):
#     SN = request.session.get("name")
#     if(request.method == "POST"):
#         user_email = request.session.get("email")
#         userObj = sign.objects.get(email = user_email)
#         SA = request.POST["senderAddress"]
#         SP = request.POST["senderPhone"]
#         RN = request.POST["receiverName"]
#         RA = request.POST["receiverAddress"]
#         RP = request.POST["receiverPhone"]
#         Weight = request.POST["weight"]
#         Service = request.POST["serviceType"]
#         Rs = request.POST["money"]
#         booking(userid = userObj, name = SN, pickupAddress = SA, senderNumber = SP, recipientName = RN, recipientAddress = RA, recipientNumber = RP, package = Weight, service = Service, rs = Rs, date = datetime.now()).save()
#         messages.success(request, "Process Of Shipment is completed. We will Notify you about your rider soon on your mobile number "+ SP +" or registered mobile number and registered gmail")
#         return redirect('book')
#     return render(request, "booking.html", {"SN" : SN})

# def hist(request):
#     if(request.session.get("email")):
#         logged_in_name = request.session.get("name")
#         user_bookings = booking.objects.filter(name=logged_in_name)
#         active_shipments = user_bookings.exclude(status='delivered').order_by('-date')
#         delivered_shipments = user_bookings.filter(status='delivered').order_by('-delivered_date')
#         data = {
#             "active_shipments" : active_shipments,
#             "delivered_shipments" : delivered_shipments,
#         }
#         return render(request, "history.html", data)
#     return render(request, "history.html")

# def review(request):
    # tid = request.GET.get("id")  #Fetching id from url
    # bookingObj = get_object_or_404(booking, trackingId = tid)
    # if(request.method == "POST"):
    #     R = request.POST.get("rev")
    #     ReviewUser(booking = bookingObj, star = R, date = datetime.now()).save()
    #     messages.success(request, "Your Review has submitted.")
    #     return redirect('review')
    # return render(request, "review.html")


# def bill(request):
#     user_email = request.session.get("email")
#     if not user_email:
#         messages.error(request, "You have to login first.")
#         return redirect("signup")   # or your login/signup url name
#     try:
#         user_obj = sign.objects.get(email=user_email)
#     except sign.DoesNotExist:
#         messages.error(request, "User not found. Please login again.")
#         return redirect("signup")

#     # all invoices for this user
#     invoices = Invoice.objects.filter(user=user_obj).order_by("-created_at")
#     payment_methods = PaymentMethod.objects.filter(user=user_obj).order_by("-created_at")
#     context = {
#         "invoices": invoices,
#         "payment_methods": payment_methods,
#     }
#     return render(request, "bill.html", context)

# def profile(request):
#     name = request.session.get("name")
#     email = request.session.get("email")
#     number = request.session.get("number")
#     address = request.session.get("address")
#     image = request.session.get("image")
#     data = {
#         'name' : name,
#         'email' : email,
#         'number' : number,
#         'address' : address,
#         'image' : image,
#     }
#     return render(request, "profile.html", data)

# def helpCenter(request):
    # return render(request, "help.html")
