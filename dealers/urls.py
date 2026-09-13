from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.register, name="dealer-register"),
    path("dashboard/", views.dashboard, name="dealer-dashboard"),
    path("cylinders/receive/", views.receive_cylinders, name="dealer-receive-cylinders"),
    path("allocations/create/", views.create_allocation_run, name="dealer-create-allocation"),
    path("coverage/", views.manage_coverage, name="dealer-manage-coverage"),
]
