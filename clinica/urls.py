# Trabalho-PDS/clinica/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views # ADICIONE ESTA LINHA
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', auth_views.LoginView.as_view(template_name='clinica/login.html'), name='login'),
    path('home/', views.home, name='home'),
    path('dashboard/', views.home, name='dashboard'),
    path('buscar_paciente/', views.buscar_paciente, name='buscar_paciente'),
    path('buscar_medico/', views.buscar_medico, name='buscar_medico'),
    path('sair/', views.sair, name='logout'),
    path('novo_paciente/', views.novo_paciente, name='novo_paciente'),
    path('agendar_consulta/', views.agendar_consulta, name='agendar_consulta'),
    path('meus_pacientes/', views.meus_pacientes, name='meus_pacientes'),
    path('consultas/', views.consultas_medico, name='consultas_medico'),
]