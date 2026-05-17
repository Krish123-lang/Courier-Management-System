from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('home/', views.home, name="home"),
    path('contact/',views.contact, name="contact"),
    path('login/', views.login, name="login"),
    path('signup/', views.signup, name="signup"),
    path('dom/', views.dom, name="dom"),
    path('vas/', views.vas, name="vas"),
    path('about/', views.about, name="about"),
    path('team/', views.team, name="team"),
]
