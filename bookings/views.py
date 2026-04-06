from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import date, datetime
import calendar

from .models import Service, Appointment
from .forms import CustomUserCreationForm
from .availability import active_appointments, booking_conflicts, unavailable_slots_by_date


# ─────────────────────────────────────────────────────────────────────────────
# CORE PAGES
# ─────────────────────────────────────────────────────────────────────────────

def home(request):
    return render(request, 'catalog/home.html')


def service_catalog(request):
    all_services = Service.objects.all()
    context = {'services': all_services}
    return render(request, 'catalog/service_list.html', context)


def register_request(request):
    """
    Registration view using CustomUserCreationForm (Improvement B).
    Saves email to the User model so it can be pre-filled at booking time.
    """
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Save email to the User model (Improvement B)
            user.email = form.cleaned_data.get('email', '')
            user.save()
            login(request, user)
            return redirect("catalog")
    else:
        form = CustomUserCreationForm()
    return render(request, "catalog/register.html", {"form": form})


# ─────────────────────────────────────────────────────────────────────────────
# BOOKING FLOW — STEP A: Choose date / time / phone / requests
# ─────────────────────────────────────────────────────────────────────────────

# Month rendered on the booking calendar (catalog/book.html); keep in sync.
_BOOKING_CALENDAR_YEAR = 2026
_BOOKING_CALENDAR_MONTH = 4


@login_required
def book_service(request, service_id):
    """
    Step A — Shows the booking form (date, time, phone, special requests).
    On POST, saves validated data to the session and redirects to the summary.
    """
    service = get_object_or_404(Service, id=service_id)

    _, last_day = calendar.monthrange(_BOOKING_CALENDAR_YEAR, _BOOKING_CALENDAR_MONTH)
    calendar_dates = [
        date(_BOOKING_CALENDAR_YEAR, _BOOKING_CALENDAR_MONTH, d)
        for d in range(1, last_day + 1)
    ]
    appts_month = list(
        active_appointments().filter(
            date__year=_BOOKING_CALENDAR_YEAR,
            date__month=_BOOKING_CALENDAR_MONTH,
        )
    )
    unavailable_by_date = unavailable_slots_by_date(
        calendar_dates, service.duration_minutes, appts_month
    )
    today = timezone.now().date()
    booking_calendar_payload = {
        'unavailable': unavailable_by_date,
        'minDate': today.isoformat(),
    }

    if request.method == 'POST':
        selected_date = request.POST.get('date')
        selected_time = request.POST.get('time')
        client_phone   = request.POST.get('phone_number')
        client_requests = request.POST.get('special_requests', '')

        if selected_date and selected_time and client_phone:
            try:
                parsed_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
                parsed_time = datetime.strptime(
                    selected_time.strip(), "%I:%M %p"
                ).time()
            except ValueError:
                messages.error(request, 'Invalid date or time.')
            else:
                day_appts = list(active_appointments().filter(date=parsed_date))
                if booking_conflicts(
                    parsed_date,
                    parsed_time,
                    service.duration_minutes,
                    day_appts,
                ):
                    messages.error(
                        request,
                        'That time overlaps another appointment. Please choose a different slot.',
                    )
                else:
                    # Store in session — NOT saved to DB yet
                    request.session['pending_booking'] = {
                        'service_id': service_id,
                        'date':       selected_date,
                        'time':       selected_time,
                        'phone':      client_phone,
                        'requests':   client_requests,
                    }
                    return redirect('booking_summary')
        else:
            messages.error(request, 'Please fill in all required fields.')

    return render(request, 'catalog/book.html', {
        'service': service,
        'booking_calendar_payload': booking_calendar_payload,
    })


# ─────────────────────────────────────────────────────────────────────────────
# BOOKING FLOW — STEP B: Review summary, enter email, confirm
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def booking_summary(request):
    """
    Step B — Shows a summary of the pending booking.
    Email is pre-filled from the user's profile (Improvement B).
    On confirm POST: saves the appointment, sends an HTML confirmation email
    (Improvement C), and renders the status page.
    """
    pending = request.session.get('pending_booking')

    if not pending:
        messages.error(request, 'No pending booking found. Please start again.')
        return redirect('catalog')

    service = get_object_or_404(Service, id=pending['service_id'])

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'edit':
            # Return user to the booking form; session data stays intact
            return redirect('book_service', service_id=service.id)

        if action == 'confirm':
            client_email = request.POST.get('email', '').strip()

            # Parse date/time from session
            parsed_date = datetime.strptime(pending['date'], "%Y-%m-%d").date()
            parsed_time = datetime.strptime(pending['time'], "%I:%M %p").time()

            day_appts = list(active_appointments().filter(date=parsed_date))
            if booking_conflicts(
                parsed_date,
                parsed_time,
                service.duration_minutes,
                day_appts,
            ):
                messages.error(
                    request,
                    'That time was just taken. Please go back and pick another slot.',
                )
                return render(request, 'catalog/booking_summary.html', {
                    'service':    service,
                    'pending':    pending,
                    'user_email': request.user.email,
                })

            # Save appointment to DB
            appointment = Appointment.objects.create(
                user=request.user,
                service=service,
                date=parsed_date,
                start_time=parsed_time,
                phone_number=pending['phone'],
                special_requests=pending.get('requests', ''),
                email=client_email,
                status='confirmed',
            )

            # Clear session
            del request.session['pending_booking']

            # Send HTML confirmation email (Improvement C)
            email_sent = False
            if client_email:
                email_sent = _send_confirmation_email(request, appointment, service, client_email)

            return render(request, 'catalog/booking_confirmed.html', {
                'appointment':  appointment,
                'service':      service,
                'email_sent':   email_sent,
                'client_email': client_email,
            })

    # GET — display the summary page; pre-fill email from user's profile (Improvement B)
    return render(request, 'catalog/booking_summary.html', {
        'service':    service,
        'pending':    pending,
        'user_email': request.user.email,
    })


# ─────────────────────────────────────────────────────────────────────────────
# MY APPOINTMENTS — view + cancel (Improvement D)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def my_appointments(request):
    """Improvement D — Shows all of the user's appointments with status badges."""
    appointments = (
        Appointment.objects.filter(user=request.user)
        .exclude(status='cancelled')
        .select_related('service')
        .order_by('-date', '-start_time')
    )
    today = timezone.now().date()
    return render(request, 'catalog/my_appointments.html', {
        'appointments': appointments,
        'today':        today,
    })


@login_required
def cancel_appointment(request, pk):
    """
    Permanently removes the appointment (client and admin), frees the time slot,
    and sends a cancellation email when an address is on file.
    """
    appointment = get_object_or_404(Appointment, pk=pk, user=request.user)

    if appointment.status != 'cancelled' and appointment.email:
        _send_cancellation_email(appointment)

    appointment.delete()
    messages.success(
        request,
        'Your appointment has been cancelled. The time slot is available again.',
    )
    return redirect('my_appointments')


# ─────────────────────────────────────────────────────────────────────────────
# EMAIL HELPERS (Improvement C — HTML email via EmailMultiAlternatives)
# ─────────────────────────────────────────────────────────────────────────────

def _send_confirmation_email(request, appointment, service, client_email):
    """Sends an HTML booking confirmation email. Returns True on success."""
    try:
        subject = f"Booking Confirmation — {service.name}"
        context = {
            'user':        request.user,
            'appointment': appointment,
            'service':     service,
        }
        html_content  = render_to_string('catalog/emails/confirmation_email.html', context)
        plain_content = (
            f"Hello {request.user.username},\n\n"
            f"Your appointment has been confirmed!\n\n"
            f"Service:  {service.name}\n"
            f"Date:     {appointment.date.strftime('%B %d, %Y')}\n"
            f"Time:     {appointment.start_time.strftime('%I:%M %p')}\n"
            f"Duration: {service.duration_minutes} minutes\n"
            f"Price:    ${service.price}\n\n"
            f"Special Requests: {appointment.special_requests or 'None'}\n\n"
            f"Thank you for booking with us!\nThe Salon Team"
        )
        msg = EmailMultiAlternatives(
            subject,
            plain_content,
            settings.DEFAULT_FROM_EMAIL,
            [client_email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return True
    except Exception:
        return False


def _send_cancellation_email(appointment):
    """Sends an HTML cancellation email. Silent on failure."""
    try:
        subject = f"Appointment Cancelled — {appointment.service.name}"
        context = {'appointment': appointment}
        html_content  = render_to_string('catalog/emails/cancellation_email.html', context)
        plain_content = (
            f"Hello {appointment.user.username},\n\n"
            f"Your appointment for {appointment.service.name} on "
            f"{appointment.date.strftime('%B %d, %Y')} at "
            f"{appointment.start_time.strftime('%I:%M %p')} has been cancelled.\n\n"
            f"If this was a mistake, please rebook through our website.\n\n"
            f"The Salon Team"
        )
        msg = EmailMultiAlternatives(
            subject,
            plain_content,
            settings.DEFAULT_FROM_EMAIL,
            [appointment.email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except Exception:
        pass