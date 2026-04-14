from django.db import models
from django.contrib.auth.models import User

class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2) 
    duration_minutes = models.IntegerField(help_text="Estimated time in minutes")
    is_active = models.BooleanField(default=True) 

    def __str__(self):
        return self.name

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

    phone_number = models.CharField(max_length=10)
    email = models.EmailField(blank=True, null=True)       
    special_requests = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='confirmed',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.start_time and self.service:
            start_dt = datetime.combine(datetime.today(), self.start_time)
            end_dt = start_dt + timedelta(minutes=self.service.duration_minutes)
            self.end_time = end_dt.time()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.service.name} on {self.date}"


class StaffDaySchedule(models.Model):
    """
    Weekly working hours for salon staff (is_staff users). Used to compute
    bookable time slots as the union of all configured staff shifts.
    Weekday follows Python: 0=Monday … 6=Sunday.
    """
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='staff_day_schedules',
    )
    weekday = models.PositiveSmallIntegerField(choices=WEEKDAY_CHOICES)
    is_working = models.BooleanField(default=True)
    opens_at = models.TimeField(blank=True, null=True)
    closes_at = models.TimeField(blank=True, null=True)

    class Meta:
        unique_together = [['user', 'weekday']]
        ordering = ['user_id', 'weekday']

    def __str__(self):
        return f"{self.user.username} — day {self.weekday}"
