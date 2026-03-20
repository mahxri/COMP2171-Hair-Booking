from django.urls import path
from . import views # <-- Only import views here!

urlpatterns = [
    path('', views.service_catalog, name='catalog'),
]