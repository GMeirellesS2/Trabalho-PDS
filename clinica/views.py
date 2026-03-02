# Trabalho-PDS/clinica/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Paciente, Medico, Consulta

def index(request):
    return render(request, 'clinica/index.html')

@login_required
def buscar_paciente(request):
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
    
    return render(request, 'clinica/buscar_paciente.html', {'pacientes': pacientes})

@login_required
def home(request):
    pacientes = Paciente.objects.all()
    total_pacientes = Paciente.objects.count()
    total_medicos = Medico.objects.count()
    total_consultas = Consulta.objects.count()
    # agora correto
    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()

    contexto = {
        'lista_pacientes': pacientes,
        'is_medico': is_medico,
        'total_pacientes': total_pacientes,
        'total_medicos': total_medicos,
        'total_consultas': total_consultas,
    }

    return render(request, 'clinica/home.html', contexto)