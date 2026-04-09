from django.contrib import admin

from .models import Service, Appointment, StaffDaySchedule


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_minutes', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'service',
        'status',
        'date',
        'start_time',
        'end_time',
        'phone_number',
        'email',
        'created_at',
    )
    list_filter = ('status', 'date', 'service')
    search_fields = (
        'user__username',
        'user__email',
        'phone_number',
        'email',
        'special_requests',
    )
    date_hierarchy = 'date'
    ordering = ('-date', '-start_time')
    readonly_fields = ('created_at',)
    show_facets = admin.ShowFacets.ALWAYS

    def has_delete_permission(self, request, obj=None):
        """
        Allow removal from the admin if the user can delete *or* change appointments.
        (Many staff accounts have change but not delete checked; salon admins expect both.)
        """
        if super().has_delete_permission(request, obj):
            return True
        opts = self.model._meta
        change_perm = f'{opts.app_label}.change_{opts.model_name}'
        return (
            request.user.is_active
            and request.user.is_staff
            and request.user.has_perm(change_perm)
        )


@admin.register(StaffDaySchedule)
class StaffDayScheduleAdmin(admin.ModelAdmin):
    list_display = ('user', 'weekday', 'is_working', 'opens_at', 'closes_at')
    list_filter = ('is_working', 'weekday')
    search_fields = ('user__username',)
    ordering = ('user_id', 'weekday')
