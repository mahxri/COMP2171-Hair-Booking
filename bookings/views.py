from django.shortcuts import render, redirect
from .models import Service
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

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