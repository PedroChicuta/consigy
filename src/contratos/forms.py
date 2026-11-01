from django import forms


class MotivoForm(forms.Form):
    motivo = forms.CharField(label='Motivo', help_text='Ex.: a averbação ou o pagamento falhou.')
