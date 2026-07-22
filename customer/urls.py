from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dash, name='dashboard'),
    path("track/", views.track, name='track'),
    path("signout/", views.signout, name='signout'),
    
    path("book/", views.book, name='book'),
    path("hist/", views.hist, name='hist'),
    path("bill/", views.bill, name='bill'),
    path("paypal/create-order/<int:invoice_id>/", views.paypal_create_order, name='paypal_create_order'),
    path("paypal/return/", views.paypal_return, name='paypal_return'),
    path("paypal/cancel/", views.paypal_cancel, name='paypal_cancel'),
    path("help/", views.helpCenter, name='help'),
    path("profile/", views.profile, name='profile'),
    path("review/", views.review, name='review'),
]
