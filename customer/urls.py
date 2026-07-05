from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dash, name='dashboard'),
    path("track/", views.track, name='track'),
    path("signout/", views.signout, name='signout'),

    path("book/", views.book, name='book'),
    path("hist/", views.hist, name='hist'),
    path("bill/", views.bill, name='bill'),
    path("help/", views.helpCenter, name='help'),
    path("profile/", views.profile, name='profile'),
    path("review/", views.review, name='review'),
    path("delivery-actions/", views.delivery_staff_actions, name='delivery_staff_actions'),
    path("delivery-actions/<int:shipment_id>/", views.delivery_staff_action, name='delivery_staff_action'),
]
