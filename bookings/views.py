from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from .models import Service
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

def home(request):
    return render(request, 'catalog/home.html')

# 1. Your original Service Catalog view
def service_catalog(request):
    # Fetch ALL services, both active and inactive
    all_services = Service.objects.all()
    
    context = {
        'services': all_services
    }
    return render(request, 'catalog/service_list.html', context)

# 2. Your new Registration view
def register_request(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Automatically log them in after registering
            return redirect("catalog")
    else:
        form = UserCreationForm()
    
    return render(request, "catalog/register.html", {"form": form})

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Service, Appointment
from datetime import datetime

@login_required # Ensures they must be logged in to reach this page
def book_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)

    # 1. HANDLE SAVING THE APPOINTMENT
    # 1. HANDLE SAVING THE APPOINTMENT
    if request.method == 'POST':
        selected_date = request.POST.get('date')
        selected_time = request.POST.get('time')
        # Catch the new inputs from the HTML form
        client_phone = request.POST.get('phone_number')
        client_requests = request.POST.get('special_requests')

        if selected_date and selected_time and client_phone:
            parsed_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
            parsed_time = datetime.strptime(selected_time, "%I:%M %p").time()

            # Save ALL the data to the database
            Appointment.objects.create(
                user=request.user,
                service=service,
                date=parsed_date,
                start_time=parsed_time,
                phone_number=client_phone,
                special_requests=client_requests
            )
            return redirect('home')

    # 2. HANDLE DISPLAYING CONFLICTS
    # Find all appointments for this specific service
    existing_bookings = Appointment.objects.filter(service=service)
    
    # Create a simple list of taken times (e.g., ["9:30 AM", "1:00 PM"]) to pass to HTML
    booked_times = [booking.start_time.strftime("%I:%M %p").lstrip('0') for booking in existing_bookings]

    return render(request, 'catalog/book.html', {
        'service': service,
        'booked_times': booked_times
    })