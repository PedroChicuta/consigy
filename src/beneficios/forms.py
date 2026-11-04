import datetime
from decimal import Decimal

from django import forms

from beneficios.models import Beneficio
from clientes.forms import DataInput


class BeneficioForm(forms.Form):
    numero = forms.CharField(label='Número do Benefício', max_length=20)
    especie = forms.ChoiceField(label='Espécie', choices=Beneficio.Especie.choices)
    margem_valor = forms.DecimalField(
        label='Valor da Margem (R$)',
        max_digits=10,
        decimal_places=2,
        required=False,
    )
    margem_data_consulta = forms.DateField(
        label='Data da consulta',
        widget=DataInput(format='%Y-%m-%d'),
        required=False,
        initial=datetime.date.today,
    )

    def clean(self):
        cleaned_data = super().clean()
        margem_valor = cleaned_data.get('margem_valor')
        margem_data_consulta = cleaned_data.get('margem_data_consulta')

        if margem_valor is not None:
            if margem_valor <= Decimal('0'):
                self.add_error('margem_valor', 'A Margem deve ser maior que zero.')
            if not margem_data_consulta:
                self.add_error('margem_data_consulta', 'Informe a data da consulta.')
            elif margem_data_consulta > datetime.date.today():
                self.add_error(
                    'margem_data_consulta', 'A data da consulta não pode estar no futuro.'
                )

        return cleaned_data


class MargemForm(forms.Form):
    valor = forms.DecimalField(label='Valor da Margem (R$)', max_digits=10, decimal_places=2)
    data_consulta = forms.DateField(
        label='Data da consulta',
        widget=DataInput(format='%Y-%m-%d'),
        initial=datetime.date.today,
    )

    def clean_valor(self):
        valor = self.cleaned_data.get('valor')
        if valor is not None and valor <= Decimal('0'):
            raise forms.ValidationError('A Margem deve ser maior que zero.')
        return valor

    def clean_data_consulta(self):
        data = self.cleaned_data.get('data_consulta')
        if data and data > datetime.date.today():
            raise forms.ValidationError('A data da consulta não pode estar no futuro.')
        return data

