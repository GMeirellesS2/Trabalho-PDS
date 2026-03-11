# Trabalho-PDS/clinica/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Paciente, Medico, Consulta, Prontuario
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.db import IntegrityError
from django.utils import timezone
from datetime import date, timedelta
from .forms import PacienteForm, MedicoForm, MedicoEditForm
from xhtml2pdf import pisa
from django.http import HttpResponse
from django.template.loader import get_template
from django.contrib.auth.models import User, Group
from django.db import transaction
from .models import Especialidade
from .forms import EspecialidadeForm

def index(request):
    return render(request, 'clinica/index.html')


@login_required
def exportar_prontuario_pdf(request, cpf):
    paciente = get_object_or_404(Paciente, cpf=cpf)
    prontuarios = Prontuario.objects.filter(cpf_paciente_pront=paciente).select_related(
        'crm_medico_pront', 'crm_medico_pront__usuario_medico'
    ).order_by('-data_registro')

    contexto = {'paciente': paciente, 'prontuarios': prontuarios}

    # 1. Pegamos o template HTML
    template = get_template('clinica/prontuario_pdf.html')
    html = template.render(contexto)

    # 2. Criamos a resposta HTTP informando que é um PDF
    response = HttpResponse(content_type='application/pdf')
    # O "attachment" faz o download direto. Se quiser que abra no navegador, mude para "inline"
    response['Content-Disposition'] = f'attachment; filename="prontuario_{paciente.cpf}.pdf"'

    # 3. Geramos o PDF com o xhtml2pdf
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Erro ao gerar o PDF', status=500)

    return response


@login_required
def agenda_medico(request, crm):
    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    # Busca o médico
    medico = get_object_or_404(Medico, crm=crm)

    # Busca as consultas filtrando pelo médico e status AGENDADO, ordenando pela data
    consultas = Consulta.objects.filter(
        crm_medico=medico,
        status=Consulta.AGENDADO
    ).select_related('cpf_paciente').order_by('data_hora')

    contexto = {
        'medico': medico,
        'consultas': consultas,
        'is_medico': is_medico,
        'is_recepcionista': is_recepcionista,
    }

    return render(request, 'clinica/agenda_medico.html', contexto)



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
    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    contexto = {
        'is_medico': is_medico,
        'is_recepcionista': is_recepcionista,
    }

    hoje = date.today()

    # ==========================================
    # DADOS DA RECEPCIONISTA / ADMIN
    # ==========================================
    if is_recepcionista or request.user.is_superuser:
        contexto['total_pacientes'] = Paciente.objects.count()
        contexto['total_medicos'] = Medico.objects.count()
        contexto['total_consultas'] = Consulta.objects.count()

        # CORREÇÃO AQUI: data_hora__date=hoje
        contexto['consultas_hoje_clinica'] = Consulta.objects.filter(data_hora__date=hoje).count()
        contexto['consultas_hoje_lista'] = Consulta.objects.filter(data_hora__date=hoje).select_related('cpf_paciente',
                                                                                                        'crm_medico__usuario_medico')

    # ==========================================
    # DADOS DO MÉDICO
    # ==========================================
    if is_medico:
        medico_logado = Medico.objects.get(usuario_medico=request.user)

        contexto['meus_pacientes_count'] = Paciente.objects.filter(
            consulta__crm_medico=medico_logado).distinct().count()

        # CORREÇÃO AQUI: data_hora__date=hoje
        contexto['minhas_consultas_hoje'] = Consulta.objects.filter(crm_medico=medico_logado, data_hora__date=hoje,
                                                                    status=Consulta.AGENDADO).count()
        contexto['minhas_consultas_pendentes'] = Consulta.objects.filter(crm_medico=medico_logado,
                                                                         status=Consulta.AGENDADO).count()

        # CORREÇÃO AQUI: data_hora__date=hoje
        contexto['consultas_hoje_lista'] = Consulta.objects.filter(crm_medico=medico_logado,
                                                                   data_hora__date=hoje).select_related('cpf_paciente')

    return render(request, 'clinica/dashboard.html', contexto)

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
def remarcar_consulta(request):

    id_consulta = request.GET.get('id')

    consulta = None
    erro = None

    if id_consulta:
        try:
            consulta = Consulta.objects.select_related(
                'cpf_paciente',
                'crm_medico'
            ).get(id_consulta=id_consulta)

        except Consulta.DoesNotExist:
            erro = "Consulta não encontrada."

    if request.method == "POST":

        id_consulta = request.POST.get('id_consulta')
        nova_data = request.POST.get('nova_data')

        consulta = Consulta.objects.get(id_consulta=id_consulta)
        consulta.data_hora = nova_data
        consulta.save()

        return redirect('dashboard')

    return render(request, 'clinica/remarcar_consulta.html', {
        'consulta': consulta,
        'erro': erro
    })

@login_required
def cancelar_consulta(request):

    id_consulta = request.GET.get('id') or request.POST.get('id_consulta')

    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    consulta = None
    erro = None

    try:
        consulta = Consulta.objects.select_related(
            'cpf_paciente',
            'crm_medico',
            'crm_medico__usuario_medico'
        ).get(id_consulta=id_consulta)

        if request.method == "POST":

            confirmar = request.POST.get('confirmar_cancelamento') == "1"

            if confirmar:
                consulta.status = Consulta.CANCELADA
                consulta.save()

                return redirect('gerenciar_consultas')

    except Consulta.DoesNotExist:
        erro = "Consulta não encontrada."

    except Exception as e:
        erro = f"Erro ao cancelar consulta: {str(e)}"

    contexto = {
        'consulta': consulta,
        'erro': erro,
        'is_medico': is_medico,
        'is_recepcionista': is_recepcionista
    }

    return render(request, 'clinica/cancelar_consulta.html', contexto)

@login_required
def agendar_consulta(request):
    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    if request.method == 'POST':
        cpf_paciente = request.POST.get('paciente')
        crm_medico = request.POST.get('medico')
        data_consulta = request.POST.get('data_hora')  # Agora vem do HTML no formato YYYY-MM-DDTHH:MM

        try:
            paciente = Paciente.objects.get(cpf=cpf_paciente)
            medico = Medico.objects.get(crm=crm_medico)

            # VERIFICAÇÃO DE CHOQUE DE HORÁRIO:
            # Busca se existe alguma consulta para este médico, neste mesmo horário, que não foi cancelada
            horario_ocupado = Consulta.objects.filter(
                crm_medico=medico,
                data_hora=data_consulta,
                status=Consulta.AGENDADO
            ).exists()

            if horario_ocupado:
                # Se o horário estiver ocupado, criamos um erro amigável e paramos a execução
                erro = "Este médico já possui uma consulta agendada exatamente para este horário. Por favor, selecione outro."
                pacientes = Paciente.objects.all().order_by('nome_paciente')
                medicos = Medico.objects.select_related('usuario_medico', 'id_especialidade').all()
                contexto = {'erro': erro, 'pacientes': pacientes, 'medicos': medicos, 'is_medico': is_medico,
                            'is_recepcionista': is_recepcionista}
                return render(request, 'clinica/agendar_consulta.html', contexto)

            # Se passar da verificação, cria o registro da consulta normalmente
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
            pacientes = Paciente.objects.all().order_by('nome_paciente')
            medicos = Medico.objects.select_related('usuario_medico', 'id_especialidade').all()
            contexto = {'erro': erro, 'pacientes': pacientes, 'medicos': medicos, 'is_medico': is_medico,
                        'is_recepcionista': is_recepcionista}
            return render(request, 'clinica/agendar_consulta.html', contexto)

    # Se for um pedido GET (apenas a abrir a tela)
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
                consulta=consulta,
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


@login_required
def prontuario_paciente(request, cpf):
    # Verifica o tipo de usuário para a sidebar
    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    # Busca o paciente pelo CPF ou retorna erro 404 se não achar
    paciente = get_object_or_404(Paciente, cpf=cpf)

    # Busca todos os prontuários desse paciente, ordenando do mais recente para o mais antigo
    prontuarios = Prontuario.objects.filter(cpf_paciente_pront=paciente).select_related(
        'consulta',
        'crm_medico_pront',
        'crm_medico_pront__usuario_medico'
    ).order_by('-data_registro')

    contexto = {
        'paciente': paciente,
        'prontuarios': prontuarios,
        'is_medico': is_medico,
        'is_recepcionista': is_recepcionista,
    }

    return render(request, 'clinica/prontuario_paciente.html', contexto)

# ==========================================
# CRUD DE PACIENTES (COM SIDEBAR CORRIGIDA)
# ==========================================

@login_required
def paciente_listar(request):
    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    pacientes = Paciente.objects.all()

    contexto = {
        'pacientes': pacientes,
        'is_medico': is_medico,
        'is_recepcionista': is_recepcionista
    }

    return render(request, 'clinica/paciente_listar.html', contexto)


@login_required
def paciente_criar(request):
    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    form = PacienteForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('paciente_listar')

    contexto = {
        'form': form,
        'is_medico': is_medico,
        'is_recepcionista': is_recepcionista
    }
    return render(request, 'clinica/paciente_form.html', contexto)


@login_required
def paciente_editar(request, cpf):
    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    paciente = get_object_or_404(Paciente, pk=cpf)
    form = PacienteForm(request.POST or None, instance=paciente)

    if form.is_valid():
        form.save()
        return redirect('paciente_listar')

    contexto = {
        'form': form,
        'is_medico': is_medico,
        'is_recepcionista': is_recepcionista
    }
    return render(request, 'clinica/paciente_form.html', contexto)


@login_required
def paciente_excluir(request, cpf):
    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    paciente = get_object_or_404(Paciente, pk=cpf)

    if request.method == "POST":
        paciente.delete()
        return redirect('paciente_listar')

    contexto = {
        'paciente': paciente,
        'is_medico': is_medico,
        'is_recepcionista': is_recepcionista
    }
    return render(request, 'clinica/paciente_delete.html', contexto)

# ==========================================
# CRUD DE MÉDICOS
# ==========================================

@login_required
def medico_listar(request):
    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    # Usamos select_related para deixar o carregamento do usuário e especialidade mais rápido
    medicos = Medico.objects.all().select_related('usuario_medico', 'id_especialidade')

    contexto = {
        'medicos': medicos,
        'is_medico': is_medico,
        'is_recepcionista': is_recepcionista
    }
    return render(request, 'clinica/medico_listar.html', contexto)


@login_required
def medico_criar(request):
    # 1. CORREÇÃO DA SIDEBAR: Adicionamos as verificações
    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    if request.method == 'POST':
        form = MedicoForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=form.cleaned_data['username'],
                        password=form.cleaned_data['password'],
                        email=form.cleaned_data['email'],
                        first_name=form.cleaned_data['nome']
                    )

                    grupo_medicos, created = Group.objects.get_or_create(name='Médicos')
                    user.groups.add(grupo_medicos)

                    medico = form.save(commit=False)
                    medico.usuario_medico = user
                    medico.save()

                    return redirect('medico_listar')

            except Exception as e:
                form.add_error(None, f"Erro ao salvar: {str(e)}")
    else:
        form = MedicoForm()

    # 2. CORREÇÃO DA SIDEBAR: Passamos as variáveis para o HTML
    contexto = {
        'form': form,
        'is_medico': is_medico,
        'is_recepcionista': is_recepcionista
    }
    return render(request, 'clinica/medico_form.html', contexto)

@login_required
def medico_editar(request, crm):
    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    # Pega o médico atual e o usuário do Django atrelado a ele
    medico = get_object_or_404(Medico, pk=crm)
    usuario_vinculado = medico.usuario_medico

    if request.method == 'POST':
        # Usamos o form de edição (sem senha)
        form = MedicoEditForm(request.POST, instance=medico)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Salva as atualizações do médico (telefone, especialidade, etc)
                    form.save()

                    # Atualiza o Usuário atrelado (caso ele mude de nome, login ou email)
                    if usuario_vinculado:
                        usuario_vinculado.username = form.cleaned_data['username']
                        usuario_vinculado.email = form.cleaned_data['email']
                        usuario_vinculado.first_name = form.cleaned_data['nome']
                        usuario_vinculado.save()

                return redirect('medico_listar')
            except Exception as e:
                form.add_error(None, f"Erro ao editar: {str(e)}")
    else:
        # Quando a página carrega, preenchemos o form com os dados do Usuário do Django
        dados_iniciais = {}
        if usuario_vinculado:
            dados_iniciais = {
                'username': usuario_vinculado.username,
                'email': usuario_vinculado.email
            }
        form = MedicoEditForm(instance=medico, initial=dados_iniciais)

    contexto = {
        'form': form,
        'is_medico': is_medico,
        'is_recepcionista': is_recepcionista
    }
    return render(request, 'clinica/medico_form.html', contexto)

@login_required
def medico_excluir(request, crm):
    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    medico = get_object_or_404(Medico, pk=crm)

    if request.method == "POST":
        medico.delete()
        return redirect('medico_listar')

    contexto = {
        'medico': medico,
        'is_medico': is_medico,
        'is_recepcionista': is_recepcionista
    }
    return render(request, 'clinica/medico_delete.html', contexto)

@login_required
def gerenciar_consultas(request):

    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    consultas = Consulta.objects.filter(
        status=Consulta.AGENDADO
    ).select_related(
        'cpf_paciente',
        'crm_medico',
        'crm_medico__usuario_medico'
    ).order_by('data_hora')

    contexto = {
        'consultas': consultas,
        'is_medico': is_medico,
        'is_recepcionista': is_recepcionista
    }

    return render(request, 'clinica/gerenciar_consultas.html', contexto)

@login_required
def especialidade_listar(request):

    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    especialidades = Especialidade.objects.all()

    contexto = {
        'especialidades': especialidades,
        'is_medico': is_medico,
        'is_recepcionista': is_recepcionista
    }

    return render(request, 'clinica/especialidade_listar.html', contexto)

@login_required
def especialidade_criar(request):

    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    form = EspecialidadeForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('especialidade_listar')

    contexto = {
        'form': form,
        'is_medico': is_medico,
        'is_recepcionista': is_recepcionista
    }

    return render(request, 'clinica/especialidade_form.html', contexto)

@login_required
def especialidade_editar(request, id):

    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    especialidade = get_object_or_404(Especialidade, pk=id)

    form = EspecialidadeForm(request.POST or None, instance=especialidade)

    if form.is_valid():
        form.save()
        return redirect('especialidade_listar')

    contexto = {
        'form': form,
        'is_medico': is_medico,
        'is_recepcionista': is_recepcionista
    }

    return render(request, 'clinica/especialidade_form.html', contexto)

@login_required
def especialidade_excluir(request, id):

    is_medico = Medico.objects.filter(usuario_medico=request.user).exists()
    is_recepcionista = request.user.groups.filter(name='Recepcionista').exists()

    especialidade = get_object_or_404(Especialidade, pk=id)

    if request.method == "POST":
        especialidade.delete()
        return redirect('especialidade_listar')

    contexto = {
        'especialidade': especialidade,
        'is_medico': is_medico,
        'is_recepcionista': is_recepcionista
    }

    return render(request, 'clinica/especialidade_delete.html', contexto)





