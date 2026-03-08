# Trabalho-PDS/clinica/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Paciente, Medico, Consulta
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.db import IntegrityError
from django.utils import timezone
from datetime import date, timedelta
from .forms import PacienteForm


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

@login_required
def novo_paciente(request):
    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    if request.method == 'POST':
        cpf = request.POST.get('cpf')
        nome = request.POST.get('nome_paciente')
        data_nasc = request.POST.get('data_nasc')
        email = request.POST.get('email')
        convenio = request.POST.get('convenio')

        try:
            # Remove pontos e traços do CPF antes de salvar
            cpf_limpo = ''.join(filter(str.isdigit, cpf))
            
            Paciente.objects.create(
                cpf=cpf_limpo,
                nome_paciente=nome,
                data_nasc=data_nasc if data_nasc else None, # Evita erro se a data vier vazia
                email=email,
                convenio=convenio
            )
            # Se salvar com sucesso, redireciona para a lista de pacientes
            return redirect('buscar_paciente')
            
        except IntegrityError:
            erro = "Já existe um paciente cadastrado com este CPF."
            contexto = {'erro': erro, 'is_medico': is_medico, 'is_recepcionista': is_recepcionista}
            return render(request, 'clinica/novo_paciente.html', contexto)
        except Exception as e:
            erro = f"Erro ao cadastrar: {str(e)}"
            contexto = {'erro': erro, 'is_medico': is_medico, 'is_recepcionista': is_recepcionista}
            return render(request, 'clinica/novo_paciente.html', contexto)

    # Se for GET, apenas renderiza o formulário vazio
    contexto = {'is_medico': is_medico, 'is_recepcionista': is_recepcionista}
    return render(request, 'clinica/novo_paciente.html', contexto)

@login_required
def agendar_consulta(request):
    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    if request.method == 'POST':
        cpf_paciente = request.POST.get('paciente')
        crm_medico = request.POST.get('medico')
        data_consulta = request.POST.get('data_hora')

        try:
            # Vai buscar as instâncias do Paciente e do Médico à base de dados
            paciente = Paciente.objects.get(cpf=cpf_paciente)
            medico = Medico.objects.get(crm=crm_medico)

            # Cria o registo da consulta
            Consulta.objects.create(
                cpf_paciente=paciente,
                crm_medico=medico,
                data_hora=data_consulta,
                status=Consulta.AGENDADO,
                created_at=timezone.now()
            )
            # Reencaminha para o dashboard após agendar com sucesso
            return redirect('dashboard')
            
        except Exception as e:
            erro = f"Erro ao agendar a consulta: {str(e)}"
            # Em caso de erro, volta a carregar a página com as listas
            pacientes = Paciente.objects.all().order_by('nome_paciente')
            medicos = Medico.objects.select_related('usuario_medico', 'id_especialidade').all()
            contexto = {'erro': erro, 'pacientes': pacientes, 'medicos': medicos, 'is_medico': is_medico, 'is_recepcionista': is_recepcionista}
            return render(request, 'clinica/agendar_consulta.html', contexto)

    # Se for um pedido GET (apenas a abrir o ecrã)
    pacientes = Paciente.objects.all().order_by('nome_paciente')
    medicos = Medico.objects.select_related('usuario_medico', 'id_especialidade').all()
    
    contexto = {
        'pacientes': pacientes,
        'medicos': medicos,
        'is_medico': is_medico,
        'is_recepcionista': is_recepcionista
    }
    return render(request, 'clinica/agendar_consulta.html', contexto)

@login_required
def meus_pacientes(request):
    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    # Proteção: Se não for médico, manda de volta para o dashboard
    if not is_medico:
        return redirect('dashboard')

    # Descobre quem é o médico logado
    medico_logado = Medico.objects.get(usuario_medico=request.user)
    
    # Busca pacientes que têm consultas com ESTE médico (e usa distinct para não repetir o paciente se ele tiver 5 consultas)
    pacientes = Paciente.objects.filter(consulta__crm_medico=medico_logado).distinct()

    # Mantemos o sistema de busca inteligente para o médico também
    query = request.GET.get('busca')
    if query:
        filtros = Q(nome_paciente__icontains=query) | Q(cpf__icontains=query)
        clean_query = ''.join(filter(str.isdigit, query))
        if clean_query:
            filtros |= Q(cpf__icontains=clean_query)
        pacientes = pacientes.filter(filtros)
    
    contexto = {
        'pacientes': pacientes,
        'is_medico': is_medico,
        'is_recepcionista': is_recepcionista,
    }
    
    return render(request, 'clinica/meus_pacientes.html', contexto)

@login_required
def consultas_medico(request):
    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    if not is_medico:
        return redirect('dashboard')

    medico_logado = Medico.objects.get(usuario_medico=request.user)
    
    # --- 1. LÓGICA DE SALVAR O PRONTUÁRIO (Quando o Médico clica em Salvar no Modal) ---
    if request.method == 'POST':
        id_consulta = request.POST.get('id_consulta')
        try:
            consulta = Consulta.objects.get(id_consulta=id_consulta, crm_medico=medico_logado)
            
            # Cria o Prontuário no banco de dados vinculando àquela consulta
            from .models import Prontuario # Import local para garantir
            Prontuario.objects.update_or_create(
                id_consulta_pront=consulta,
                defaults={
                    'crm_medico_pront': medico_logado,
                    'cpf_paciente_pront': consulta.cpf_paciente,
                    'historico_clinico': request.POST.get('historico_clinico'),
                    'exame_fisico': request.POST.get('exame_fisico'),
                    'diagnostico': request.POST.get('diagnostico'),
                    'prescricao': request.POST.get('prescricao'),
                    'exames_solicitados': request.POST.get('exames_solicitados'),
                    'data_registro': date.today()
                }
            )
            
            # Muda o status da consulta para "Concluída"
            consulta.status = Consulta.CONCLUIDO
            consulta.save()
            return redirect('consultas_medico') # Recarrega a página
            
        except Exception as e:
            # Se der erro, vamos enviar para a tela
            contexto_erro = {'erro': f"Erro ao salvar: {str(e)}"}
            # Não paramos o código aqui, deixamos ele carregar a lista de consultas abaixo
    
    # --- 2. LÓGICA DE FILTROS DA TELA (Hoje, Semana, Mês, Histórico) ---
    filtro = request.GET.get('filtro', 'hoje') # Por padrão, mostra 'hoje'
    hoje = date.today()
    
    # Busca base: todas as consultas deste médico
    consultas = Consulta.objects.filter(crm_medico=medico_logado).select_related('cpf_paciente')
    
    if filtro == 'hoje':
        consultas = consultas.filter(data_hora=hoje, status=Consulta.AGENDADO)
    elif filtro == 'semana':
        # Calcula o início e fim da semana atual
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        fim_semana = inicio_semana + timedelta(days=6)
        consultas = consultas.filter(data_hora__range=[inicio_semana, fim_semana], status=Consulta.AGENDADO)
    elif filtro == 'mes':
        consultas = consultas.filter(data_hora__year=hoje.year, data_hora__month=hoje.month, status=Consulta.AGENDADO)
    elif filtro == 'historico':
        # Traz apenas as consultas que já foram concluídas
        consultas = consultas.filter(status=Consulta.CONCLUIDO).order_by('-data_hora')
    elif filtro == 'todas':
        consultas = consultas.filter(status=Consulta.AGENDADO)
        
    # Ordena para a data mais próxima aparecer primeiro (exceto no histórico)
    if filtro != 'historico':
        consultas = consultas.order_by('data_hora')

    contexto = {
        'consultas': consultas,
        'filtro_atual': filtro,
        'is_medico': is_medico,
        'is_recepcionista': is_recepcionista,
    }
    
    # Se ocorreu um erro no POST, injetamos ele no contexto
    if 'contexto_erro' in locals():
        contexto.update(contexto_erro)
        
    return render(request, 'clinica/consultas_medico.html', contexto)




# LISTAR PACIENTES
def paciente_listar(request):

    pacientes = Paciente.objects.all()

    contexto = {
        'pacientes': pacientes
    }

    return render(request, 'clinica/paciente_listar.html', contexto)


# CRIAR PACIENTE
def paciente_criar(request):

    form = PacienteForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('paciente_listar')

    return render(request, 'clinica/paciente_form.html', {'form': form})


# EDITAR PACIENTE
def paciente_editar(request, cpf):

    paciente = get_object_or_404(Paciente, pk=cpf)

    form = PacienteForm(request.POST or None, instance=paciente)

    if form.is_valid():
        form.save()
        return redirect('paciente_listar')

    return render(request, 'clinica/paciente_form.html', {'form': form})


# EXCLUIR PACIENTE
def paciente_excluir(request, cpf):

    paciente = get_object_or_404(Paciente, pk=cpf)

    if request.method == "POST":
        paciente.delete()
        return redirect('paciente_listar')

    return render(request, 'clinica/paciente_delete.html', {'paciente': paciente})