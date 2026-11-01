from django import forms
from django.utils import timezone


class PagamentoForm(forms.Form):
    data_pagamento = forms.DateField(
        label='Data de pagamento',
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        error_messages={'required': 'Informe a data de pagamento.'},
    )


class MotivoForm(forms.Form):
    motivo = forms.CharField(label='Motivo', help_text='Ex.: a averbação ou o pagamento falhou.')
