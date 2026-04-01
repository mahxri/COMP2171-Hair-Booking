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
    # Added phone_number and special_requests so they show up as columns!
    list_display = ('user', 'service', 'date', 'start_time', 'end_time', 'phone_number', 'special_requests')
    list_filter = ('date', 'service')
