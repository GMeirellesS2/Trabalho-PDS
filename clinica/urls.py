# Trabalho-PDS/clinica/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views # ADICIONE ESTA LINHA
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', auth_views.LoginView.as_view(template_name='clinica/login.html'), name='login'),
    path('home/', views.home, name='home'),
]