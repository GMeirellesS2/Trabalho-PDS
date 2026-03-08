from django.db import models
from django.contrib.auth.models import User  # Importamos o usuário padrão do Django
from django.core.exceptions import ValidationError #Validar Cpf

def validar_cpf(valor):
    if len(valor) != 11 or not valor.isdigit():
        raise ValidationError("CPF deve conter exatamente 11 números\n")


class Paciente(models.Model):
    cpf = models.CharField(primary_key=True, max_length=14, validators=[validar_cpf])
    nome_paciente = models.CharField(max_length=255, blank=True, null=True)
    data_nasc = models.DateField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    convenio = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False  # Indica que a tabela já existe no banco
        db_table = 'paciente'

    def __str__(self):
        return f"{self.nome_paciente} ({self.cpf})"

class Medico(models.Model):
    crm = models.CharField(primary_key=True, max_length=20)
    # Aqui conectamos o médico ao usuário do Django (para ele fazer login)
    usuario_medico = models.OneToOneField(User, on_delete=models.SET_NULL, db_column='usuario_medico', blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    id_especialidade = models.ForeignKey('Especialidade',
    on_delete=models.DO_NOTHING,
    db_column='id_especialidade',
    verbose_name='Especialidade',
    blank=True,
    null=True)

    class Meta:
        managed = False
        db_table = 'medico'

    def __str__(self):
        return f"Dr(a). {self.usuario_medico.username if self.usuario_medico else 'Sem Usuário'} - CRM: {self.crm}"

class Consulta(models.Model):
    # Alterei DecimalField para AutoField (um ID padrão numérico) para evitar bugs visuais
    AGENDADO = "Agendada"
    CONCLUIDO = "Concluida"
    CANCELADA = "Cancelada"

    Consulta_Status = [
        (AGENDADO, "Agendada"),
        (CONCLUIDO, "Concluída"),
        (CANCELADA, "Cancelada"),
    ]
    
    id_consulta = models.AutoField(primary_key=True)
    data_hora = models.DateTimeField(blank=True, null=True)
    crm_medico = models.ForeignKey(Medico, on_delete=models.DO_NOTHING, db_column='crm_medico', blank=True, null=True)
    cpf_paciente = models.ForeignKey(Paciente, on_delete=models.DO_NOTHING, db_column='cpf_paciente', blank=True, null=True)
    status = models.CharField(max_length=9, choices = Consulta_Status, default = AGENDADO)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'consulta'

    def __str__(self):
        paciente = self.cpf_paciente.nome_paciente if self.cpf_paciente else "Sem paciente"
        return f"{paciente} - {self.data_hora}"

class Prontuario(models.Model):
    # O Django OBRIGA todo model a ter uma primary_key.
    # Como não tinha nenhuma, coloquei a id_consulta_pront como Chave Primária por enquanto.
    consulta = models.OneToOneField(Consulta,on_delete=models.DO_NOTHING,db_column='id_consulta_pront',  primary_key=True)    
    crm_medico_pront = models.ForeignKey(Medico, on_delete=models.DO_NOTHING, db_column='crm_medico_pront', blank=True, null=True)
    cpf_paciente_pront = models.ForeignKey(Paciente, on_delete=models.DO_NOTHING, db_column='cpf_paciente_pront', blank=True, null=True)
    historico_clinico = models.TextField(blank=True, null=True)
    exame_fisico = models.TextField(blank=True, null=True)
    diagnostico = models.TextField(blank=True, null=True)
    prescricao = models.TextField(blank=True, null=True)
    exames_solicitados = models.TextField(blank=True, null=True)
    data_registro = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'prontuario'

    def __str__(self):
        return f"Prontuário da Consulta {self.id_consulta_pront}"
    
class Especialidade(models.Model):

    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=150, unique=True)

    class Meta:
        managed = False
        db_table = 'especialidade'
    
    def __str__(self):
        return self.nome
    
class Recepcionista(models.Model):

    cpf=models.CharField(primary_key=True,max_length=11,validators=[validar_cpf])
    nome = models.CharField(max_length=150,blank=True,null=True)
    telefone = models.CharField(max_length=20,blank=True,null=True)
    email = models.EmailField(blank=True,null=True)

    class Meta:
        managed = False
        db_table = 'recepcionista'

    def __str__(self):
        return self.nome