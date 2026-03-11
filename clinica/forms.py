from django import forms
from .models import Paciente, Medico


class PacienteForm(forms.ModelForm):

    class Meta:
        model = Paciente
        fields = '__all__'
        #

class MedicoForm(forms.ModelForm):
    class Meta:
        model = Medico
        fields = ['crm', 'usuario_medico', 'telefone', 'id_especialidade']