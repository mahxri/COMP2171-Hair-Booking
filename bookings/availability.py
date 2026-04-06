"""
Salon-wide availability: one active appointment blocks its time window for all services.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Iterable, Optional, Set

from django.db.models import QuerySet

from .models import Appointment


# Must match the slot grid in catalog/book.html (30-minute steps, 9:00 AM – 4:30 PM).
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


def format_slot_label(t: time) -> str:
    """Label used in templates and JSON (matches strftime + lstrip used elsewhere)."""
    return datetime(2000, 1, 1, t.hour, t.minute).strftime("%I:%M %p").lstrip("0")


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
) -> Set[str]:
    """
    Set of slot labels (e.g. '9:30 AM') that cannot be used as a *start* time
    for this service length without overlapping an existing booking.
    """
    blocked: Set[str] = set()
    day_appointments = [a for a in appointments if a.date == booking_date]
    for slot in salon_slot_times():
        if booking_conflicts(
            booking_date, slot, service_duration_minutes, day_appointments
        ):
            blocked.add(format_slot_label(slot))
    return blocked


def unavailable_slots_by_date(
    dates: Iterable[date],
    service_duration_minutes: int,
    appointments: Iterable[Appointment],
) -> dict[str, list[str]]:
    """Map ISO date string -> sorted list of unavailable slot labels."""
    appts_list = list(appointments)
    out: dict[str, list[str]] = {}
    for d in dates:
        labels = unavailable_slot_labels_for_service(
            d, service_duration_minutes, appts_list
        )
        out[d.isoformat()] = sorted(labels)
    return out
