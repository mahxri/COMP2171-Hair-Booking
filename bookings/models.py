from django.db import models
from django.contrib.auth.models import User

# This satisfies Feature 11.0 and Feature 2.0
class Service(models.Model):
    # Mandatory fields based on your SRS
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    # Decimal field ensures the two decimal places requirement for pricing
    price = models.DecimalField(max_digits=8, decimal_places=2) 
    duration_minutes = models.IntegerField(help_text="Estimated time in minutes")
    is_active = models.BooleanField(default=True) 

    def __str__(self):
        return self.name

# This prepares you for Feature 1.0 and Feature 4.0
class Appointment(models.Model):
    # models.RESTRICT prevents deleting a service that has an active booking attached to it
    service = models.ForeignKey(Service, on_delete=models.RESTRICT)
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    
    appointment_date = models.DateField()
    appointment_time = models.TimeField()

    STATUS_CHOICES = [
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONFIRMED')

    # Allows clients to input allergies/sensitivities for safety compliance
    client_notes_allergies = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.username} - {self.service.name} on {self.appointment_date}"