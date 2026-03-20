from django.contrib import admin
from .models import Service, Appointment

# This registers the Service model and customizes how it looks in the admin panel
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_minutes', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

# This registers the Appointment model for when you build that feature later
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('client', 'service', 'appointment_date', 'appointment_time', 'status')
    list_filter = ('status', 'appointment_date')