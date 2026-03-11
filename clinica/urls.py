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
    path('paciente/<str:cpf>/prontuario/', views.prontuario_paciente, name='prontuario_paciente'),
    path('medico/<path:crm>/agenda/', views.agenda_medico, name='agenda_medico'),
    path('paciente/<str:cpf>/prontuario/pdf/', views.exportar_prontuario_pdf, name='exportar_prontuario_pdf'),
    path('agendar_consulta/', views.agendar_consulta, name='agendar_consulta'),
    path('meus_pacientes/', views.meus_pacientes, name='meus_pacientes'),
    path('consultas/', views.consultas_medico, name='consultas_medico'),
    path('pacientes/', views.paciente_listar, name='paciente_listar'),
    path('pacientes/criar/', views.paciente_criar, name='paciente_criar'),
    path('pacientes/editar/<str:cpf>/', views.paciente_editar, name='paciente_editar'),
    path('pacientes/excluir/<str:cpf>/', views.paciente_excluir, name='paciente_excluir'),
    path('remarcar_consulta/', views.remarcar_consulta, name='remarcar_consultas'),
    path('cancelar_consulta/', views.cancelar_consulta, name='cancelar_consulta'),
    
    path('medicos/', views.medico_listar, name='medico_listar'),
    path('medicos/novo/', views.medico_criar, name='medico_criar'),
    path('medicos/editar/<path:crm>/', views.medico_editar, name='medico_editar'),
    path('medicos/excluir/<path:crm>/', views.medico_excluir, name='medico_excluir'),
    path('gerenciar_consultas/', views.gerenciar_consultas, name='gerenciar_consultas'),
]