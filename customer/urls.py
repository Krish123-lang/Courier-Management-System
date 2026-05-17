from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dash, name='dashboard'),
    path("track/", views.track, name='track'),
    path("signout/", views.signout, name='signout'),
]
