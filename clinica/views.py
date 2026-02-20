from django.shortcuts import render
from .models import Paciente  # <-- Importamos o modelo de Paciente


def home(request):
    # Pede ao Django para buscar TODOS os pacientes lá no Supabase
    pacientes = Paciente.objects.all()

    # Criamos um "pacote" (contexto) para enviar esses dados para o HTML
    contexto = {
        'lista_pacientes': pacientes
    }

    # Passamos o contexto como terceiro argumento
    return render(request, 'clinica/index.html', contexto)