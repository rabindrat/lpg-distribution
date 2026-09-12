from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.register, name="dealer-register"),
    path("dashboard/", views.dashboard, name="dealer-dashboard"),
]
