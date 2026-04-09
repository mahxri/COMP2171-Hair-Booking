# Generated manually (StaffDaySchedule model)

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bookings', '0004_appointment_email_appointment_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='StaffDaySchedule',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID',
                )),
                ('weekday', models.PositiveSmallIntegerField()),
                ('is_working', models.BooleanField(default=True)),
                ('opens_at', models.TimeField(blank=True, null=True)),
                ('closes_at', models.TimeField(blank=True, null=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='staff_day_schedules',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['user_id', 'weekday'],
                'unique_together': {('user', 'weekday')},
            },
        ),
    ]
