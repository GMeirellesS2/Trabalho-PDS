from django import forms
from .models import Paciente, Medico


class PacienteForm(forms.ModelForm):

    class Meta:
        model = Paciente
        fields = '__all__'
        #

class MedicoForm(forms.ModelForm):
    # Campos virtuais (não estão no Medico, mas usaremos para criar o User do Django)
    username = forms.CharField(max_length=150, required=True, label="Nome de Usuário (Login)")
    password = forms.CharField(widget=forms.PasswordInput, required=True, label="Senha")
    email = forms.EmailField(required=False, label="E-mail")

    class Meta:
        model = Medico
        # Tiramos o 'usuario_medico' e colocamos o 'nome'
        fields = ['crm', 'nome', 'telefone', 'id_especialidade']