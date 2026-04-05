"""
Improvement A — Daily Reminder Emails via APScheduler.

This module is imported in BookingsConfig.ready() so the scheduler
starts automatically when Django starts (with the dev server or in production).

The scheduler sends a reminder email to every user who has an appointment
scheduled for tomorrow.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)


def send_reminder_emails():
    """
    Queries all confirmed appointments happening tomorrow and sends each
    client a reminder email if an email address is stored on the appointment.
    """
    # Import here to avoid calling the ORM before Django is ready
    from .models import Appointment

    tomorrow = timezone.now().date() + timezone.timedelta(days=1)

    upcoming = Appointment.objects.filter(
        date=tomorrow,
        status='confirmed',
        email__isnull=False,
    ).exclude(email='').select_related('service', 'user')

    for appt in upcoming:
        try:
            subject  = f"Reminder: Your appointment is tomorrow — {appt.service.name}"
            context  = {'appointment': appt}
            html_body = render_to_string('catalog/emails/reminder_email.html', context)
            plain_body = (
                f"Hello {appt.user.username},\n\n"
                f"This is a friendly reminder that you have an appointment tomorrow!\n\n"
                f"Service:  {appt.service.name}\n"
                f"Date:     {appt.date.strftime('%B %d, %Y')}\n"
                f"Time:     {appt.start_time.strftime('%I:%M %p')}\n"
                f"Duration: {appt.service.duration_minutes} minutes\n"
                f"Price:    ${appt.service.price}\n\n"
                f"We look forward to seeing you!\nThe Salon Team"
            )
            msg = EmailMultiAlternatives(
                subject,
                plain_body,
                settings.DEFAULT_FROM_EMAIL,
                [appt.email],
            )
            msg.attach_alternative(html_body, "text/html")
            msg.send()
            logger.info(f"Reminder sent to {appt.email} for appointment {appt.pk}")
        except Exception as e:
            logger.error(f"Failed to send reminder for appointment {appt.pk}: {e}")


def delete_old_job_executions(max_age=604_800):
    """Remove APScheduler job execution records older than max_age seconds (default: 1 week)."""
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


def start():
    """Start the APScheduler background scheduler."""
    scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # Send reminder emails at 9 AM every day
    scheduler.add_job(
        send_reminder_emails,
        trigger=CronTrigger(hour=9, minute=0),
        id="send_reminder_emails",
        replace_existing=True,
    )

    # Clean up old execution logs weekly
    scheduler.add_job(
        delete_old_job_executions,
        trigger=CronTrigger(day_of_week="mon", hour=0, minute=0),
        id="delete_old_job_executions",
        replace_existing=True,
    )

    logger.info("Starting APScheduler for reminder emails...")
    scheduler.start()
