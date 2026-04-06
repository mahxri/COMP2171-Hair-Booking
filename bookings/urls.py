from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Core pages
    path('', views.home, name='home'),
    path('services/', views.service_catalog, name='catalog'),

    # Booking Flow (Feature 8.0 — two-step)
    path('book/<int:service_id>/', views.book_service, name='book_service'),
    path('booking/summary/', views.booking_summary, name='booking_summary'),

    # My Appointments + Cancellation (Improvement D)
    path('appointments/', views.my_appointments, name='my_appointments'),
    path('appointments/cancel/<int:pk>/', views.cancel_appointment, name='cancel_appointment'),

    # Authentication
    path('register/', views.register_request, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='catalog/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]