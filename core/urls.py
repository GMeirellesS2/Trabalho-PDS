# Trabalho-PDS/core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views # Importante!

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='clinica/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', include('clinica.urls')),
]