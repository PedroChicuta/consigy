from django import forms

from beneficios.models import Beneficio
from clientes.forms import DataInput


class BeneficioForm(forms.Form):
    numero = forms.CharField(label='Número do Benefício', max_length=20)
    especie = forms.ChoiceField(label='Espécie', choices=Beneficio.Especie.choices)


class MargemForm(forms.Form):
    valor = forms.DecimalField(label='Valor da Margem (R$)', max_digits=10, decimal_places=2)
    data_consulta = forms.DateField(label='Data da consulta', widget=DataInput(format='%Y-%m-%d'))
