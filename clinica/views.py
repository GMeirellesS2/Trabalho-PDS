# Trabalho-PDS/clinica/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Paciente, Medico, Consulta
from django.contrib.auth import logout
from django.shortcuts import redirect

def index(request):
    return render(request, 'clinica/index.html')

@login_required
def buscar_paciente(request):
    # Verifica o tipo de usuário logado
    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    query = request.GET.get('busca')
    
    if query:
        # Filtro base: Busca pelo nome exato ou pelo que foi digitado no CPF
        filtros = Q(nome_paciente__icontains=query) | Q(cpf__icontains=query)
        
        # Tenta extrair apenas os números (caso o usuário tenha digitado um CPF com pontos)
        clean_query = ''.join(filter(str.isdigit, query))
        
        # Só adiciona a regra do CPF limpo se a pessoa digitou algum número!
        if clean_query:
            filtros |= Q(cpf__icontains=clean_query)
            
        # Aplica os filtros construídos
        pacientes = Paciente.objects.filter(filtros)
    else:
        pacientes = Paciente.objects.all()
    
    contexto = {
        'pacientes': pacientes,
        'is_medico': is_medico,
        'is_recepcionista': is_recepcionista,
    }
    
    return render(request, 'clinica/buscar_paciente.html', contexto)

@login_required
def home(request):
    pacientes = Paciente.objects.all()
    total_pacientes = Paciente.objects.count()
    total_medicos = Medico.objects.count()
    total_consultas = Consulta.objects.count()
    
    # Verifica o tipo de usuário logado
    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    contexto = {
        'lista_pacientes': pacientes,
        'is_medico': is_medico,
        'is_recepcionista': is_recepcionista,
        'total_pacientes': total_pacientes,
        'total_medicos': total_medicos,
        'total_consultas': total_consultas,
    }

    return render(request, 'clinica/home.html', contexto)

@login_required
def buscar_medico(request):
    # Verifica o tipo de usuário logado para a sidebar
    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    query = request.GET.get('busca')
    
    if query:
        # Busca por CRM, Nome de usuário, ou Nome da Especialidade
        filtros = (
            Q(crm__icontains=query) | 
            Q(usuario_medico__username__icontains=query) |
            Q(usuario_medico__first_name__icontains=query) |
            Q(id_especialidade__nome__icontains=query)
        )
        # select_related deixa a busca no banco muito mais rápida
        medicos = Medico.objects.filter(filtros).select_related('usuario_medico', 'id_especialidade')
    else:
        medicos = Medico.objects.all().select_related('usuario_medico', 'id_especialidade')
    
    contexto = {
        'medicos': medicos,
        'is_medico': is_medico,
        'is_recepcionista': is_recepcionista,
    }
    
    return render(request, 'clinica/buscar_medico.html', contexto)

def sair(request):
    logout(request) # Encerra a sessão do usuário
    return redirect('login') # Manda ele de volta para a tela de login