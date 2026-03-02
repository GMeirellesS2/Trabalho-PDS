# Trabalho-PDS/clinica/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Paciente, Medico
from django.shortcuts import render

def index(request):
    return render(request, 'clinica/index.html')

@login_required
def home(request):
    pacientes = Paciente.objects.all()

    # agora correto
    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()

    contexto = {
        'lista_pacientes': pacientes,
        'is_medico': is_medico,
    }

    return render(request, 'clinica/home.html', contexto)

