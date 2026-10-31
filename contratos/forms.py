from django import forms


class MotivoForm(forms.Form):
    motivo = forms.CharField(label='Motivo')
