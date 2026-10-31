from django import forms


class DataInput(forms.DateInput):
    input_type = 'date'


class ClienteForm(forms.Form):
    nome = forms.CharField(max_length=150)
    telefone = forms.CharField(max_length=20)
    email = forms.EmailField(label='E-mail', required=False)


class NovoClienteForm(ClienteForm):
    cpf = forms.CharField(label='CPF', max_length=14)
    data_nascimento = forms.DateField(
        label='Data de nascimento', widget=DataInput(format='%Y-%m-%d')
    )
