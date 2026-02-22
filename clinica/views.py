# Trabalho-PDS/clinica/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Paciente, Medico # Importe Medico para verificar o cargo

@login_required
def home(request):
    pacientes = Paciente.objects.all()
    
    # Verifica se o usuário logado está vinculado a um Médico
    # O modelo Medico tem uma OneToOneField com o User chamada 'usuario_medico'
    is_medico = Medico.objects.filter(usuario_medico=request.user.username).exists()

    contexto = {
        'lista_pacientes': pacientes,
        'is_medico': is_medico,
    }

    return render(request, 'clinica/index.html', contexto)