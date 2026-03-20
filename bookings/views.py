from django.shortcuts import render
from .models import Service # <-- This is where this import belongs!

def service_catalog(request):
    active_services = Service.objects.filter(is_active=True)
    
    context = {
        'services': active_services
    }
    return render(request, 'catalog/service_list.html', context)