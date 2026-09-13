from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("offline/", views.offline, name="offline"),
    path("register/", views.register, name="register"),
    path("login/", views.user_login, name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("complaint/", views.complaint, name="complaint"),
    path("household/", views.household, name="household"),
    path("apply/", views.apply, name="apply"),
]
