"""
Salon-wide availability: one active appointment blocks its time window for all services.
Bookable start times also respect staff working hours (union across staff who saved schedules).
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Iterable, Optional, Set

from django.contrib.auth.models import User
from django.db.models import QuerySet

from .models import Appointment, StaffDaySchedule


# Must match the classic booking grid (30-minute steps, 9:00 AM – 4:30 PM start times).
def salon_slot_times() -> list[time]:
    slots: list[time] = []
    t = time(9, 0)
    end_limit = time(16, 30)
    while True:
        slots.append(t)
        if t == end_limit:
            break
        dt = datetime.combine(date.min, t) + timedelta(minutes=30)
        t = dt.time()
    return slots


# Wider grid for the booking UI and for marking outside-hours slots as unavailable.
def extended_slot_times() -> list[time]:
    slots: list[time] = []
    t = time(7, 0)
    end_limit = time(20, 30)
    while True:
        slots.append(t)
        if t == end_limit:
            break
        dt = datetime.combine(date.min, t) + timedelta(minutes=30)
        t = dt.time()
    return slots


def format_slot_label(t: time) -> str:
    """Label used in templates and JSON (matches strftime + lstrip used elsewhere)."""
    return datetime(2000, 1, 1, t.hour, t.minute).strftime("%I:%M %p").lstrip("0")


def slot_starts_fitting_shift(
    opens: time, closes: time, duration_minutes: int
) -> list[time]:
    """30-minute start times where the service fits entirely before `closes`."""
    out: list[time] = []
    cur = datetime.combine(date.min, opens)
    end_close = datetime.combine(date.min, closes)
    step = timedelta(minutes=30)
    while cur + timedelta(minutes=duration_minutes) <= end_close:
        out.append(cur.time())
        cur += step
    return out


def _staff_users_with_saved_schedules() -> QuerySet[User]:
    uids = StaffDaySchedule.objects.values_list('user_id', flat=True).distinct()
    return User.objects.filter(pk__in=uids, is_staff=True, is_active=True)


def bookable_slot_labels_for_date(
    booking_date: date, service_duration_minutes: int
) -> Set[str]:
    """
    Start-time labels a client may book on this date for the given duration.
    If no staff have saved schedules yet, uses the legacy Mon–Sat / Sun-closed grid.
    Otherwise uses the union of all configured staff shifts that day.
    """
    wd = booking_date.weekday()
    staff = _staff_users_with_saved_schedules()
    if not staff.exists():
        if wd == 6:
            return set()
        return {format_slot_label(t) for t in salon_slot_times()}

    labels: Set[str] = set()
    for user in staff:
        row = (
            StaffDaySchedule.objects.filter(user=user, weekday=wd)
            .only('is_working', 'opens_at', 'closes_at')
            .first()
        )
        if (
            not row
            or not row.is_working
            or row.opens_at is None
            or row.closes_at is None
            or row.opens_at >= row.closes_at
        ):
            continue
        for t in slot_starts_fitting_shift(
            row.opens_at, row.closes_at, service_duration_minutes
        ):
            labels.add(format_slot_label(t))
    return labels


def active_appointments() -> QuerySet[Appointment]:
    return Appointment.objects.exclude(status="cancelled").select_related("service")


def appointment_window(appt: Appointment) -> tuple[datetime, datetime]:
    """Start/end datetimes on the appointment's date."""
    d = appt.date
    start = datetime.combine(d, appt.start_time)
    if appt.end_time:
        end = datetime.combine(d, appt.end_time)
    else:
        end = start + timedelta(minutes=appt.service.duration_minutes)
    return start, end


def proposed_window(
    booking_date: date, start_time: time, duration_minutes: int
) -> tuple[datetime, datetime]:
    start = datetime.combine(booking_date, start_time)
    end = start + timedelta(minutes=duration_minutes)
    return start, end


def intervals_overlap(
    a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime
) -> bool:
    return a_start < b_end and b_start < a_end


def booking_conflicts(
    booking_date: date,
    start_time: time,
    duration_minutes: int,
    appointments: Iterable[Appointment],
    exclude_appointment_id: Optional[int] = None,
) -> bool:
    """True if the proposed booking overlaps any existing active appointment on that day."""
    p_start, p_end = proposed_window(booking_date, start_time, duration_minutes)
    for appt in appointments:
        if appt.date != booking_date:
            continue
        if exclude_appointment_id is not None and appt.pk == exclude_appointment_id:
            continue
        e_start, e_end = appointment_window(appt)
        if intervals_overlap(p_start, p_end, e_start, e_end):
            return True
    return False


def unavailable_slot_labels_for_service(
    booking_date: date,
    service_duration_minutes: int,
    appointments: Iterable[Appointment],
    exclude_appointment_id: Optional[int] = None,
) -> Set[str]:
    """
    Set of slot labels (e.g. '9:30 AM') that cannot be used as a *start* time
    on this date: outside staff hours, or overlapping an existing booking.
    """
    bookable = bookable_slot_labels_for_date(booking_date, service_duration_minutes)
    blocked: Set[str] = set()
    day_appointments = [a for a in appointments if a.date == booking_date]
    for slot in extended_slot_times():
        label = format_slot_label(slot)
        if label not in bookable:
            blocked.add(label)
            continue
        if booking_conflicts(
            booking_date,
            slot,
            service_duration_minutes,
            day_appointments,
            exclude_appointment_id=exclude_appointment_id,
        ):
            blocked.add(label)
    return blocked


def unavailable_slots_by_date(
    dates: Iterable[date],
    service_duration_minutes: int,
    appointments: Iterable[Appointment],
    exclude_appointment_id: Optional[int] = None,
) -> dict[str, list[str]]:
    """Map ISO date string -> sorted list of unavailable slot labels."""
    appts_list = list(appointments)
    out: dict[str, list[str]] = {}
    for d in dates:
        labels = unavailable_slot_labels_for_service(
            d,
            service_duration_minutes,
            appts_list,
            exclude_appointment_id=exclude_appointment_id,
        )
        out[d.isoformat()] = sorted(labels)
    return out


def is_slot_allowed_by_staff_hours(
    booking_date: date, start_time: time, service_duration_minutes: int
) -> bool:
    label = format_slot_label(start_time)
    return label in bookable_slot_labels_for_date(
        booking_date, service_duration_minutes
    )
