from django import forms


class BancoForm(forms.Form):
    nome = forms.CharField(max_length=100)
    codigo = forms.CharField(label='Código', max_length=10)
