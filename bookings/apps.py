from django.apps import AppConfig


class BookingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bookings'

    def ready(self):
        """
        Called once when Django fully starts up.
        Imports and starts the APScheduler for daily reminder emails (Improvement A).
        The try/except prevents errors if the app is imported multiple times (e.g. during tests).
        """
        try:
            from . import scheduler
            scheduler.start()
        except Exception:
            pass
