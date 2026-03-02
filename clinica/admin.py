from django.contrib import admin
from .models import Paciente, Medico, Consulta, Prontuario, Recepcionista, Especialidade

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    # Quais colunas vão aparecer na lista
    list_display = ('cpf', 'nome_paciente', 'email', 'convenio')
    # Adiciona uma barra de pesquisa
    search_fields = ('nome_paciente', 'cpf')

@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    list_display = ('crm', 'usuario_medico', 'id_especialidade', 'telefone')
    search_fields = ('crm', 'id_especialidade__nome')
    list_filter = ('id_especialidade',) # Filtro lateral por especialidade

@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ('id_consulta', 'data_hora', 'crm_medico', 'cpf_paciente', 'status')
    list_filter = ('status', 'data_hora') # Filtros laterais
    search_fields = ('cpf_paciente__nome_paciente', 'crm_medico__crm')

@admin.register(Prontuario)
class ProntuarioAdmin(admin.ModelAdmin):
    list_display = ('consulta', 'data_registro', 'crm_medico_pront', 'cpf_paciente_pront')
    list_filter = ('data_registro',)

@admin.register(Recepcionista)
class RecepcionistaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'telefone')

@admin.register(Especialidade)
class EspecialidadeAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome')