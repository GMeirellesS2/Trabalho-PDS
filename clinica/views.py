# Trabalho-PDS/clinica/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Paciente, Medico, Consulta
from django.shortcuts import render

def index(request):
    return render(request, 'clinica/index.html')
    

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

