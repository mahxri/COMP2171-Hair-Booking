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
from datetime import datetime, timedelta

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(blank=True, null=True)

    # --- CLIENT CONTACT FIELDS ---
    phone_number = models.CharField(max_length=10)
    email = models.EmailField(blank=True, null=True)       # Feature 8.0 — confirmation email
    special_requests = models.TextField(blank=True, null=True)

    # --- STATUS FIELD (Improvement D) ---
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='confirmed',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # (Keep your existing automatic end_time calculation here!)
        if self.start_time and self.service:
            start_dt = datetime.combine(datetime.today(), self.start_time)
            end_dt = start_dt + timedelta(minutes=self.service.duration_minutes)
            self.end_time = end_dt.time()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.service.name} on {self.date}"
    