from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # The new Home Page is now the root
    path('', views.home, name='home'),
    
    # The Catalog is moved to /services/
    path('services/', views.service_catalog, name='catalog'),

    path('book/<int:service_id>/', views.book_service, name='book_service'),
    
    # Authentication Routes (unchanged)
    path('register/', views.register_request, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='catalog/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]