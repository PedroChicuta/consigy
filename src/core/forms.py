from django import forms


class FormularioExemplo(forms.Form):
    """Usado só na página /design/ para mostrar o padrão de formulários (ADR 0010)."""

    nome = forms.CharField(label='Nome', initial='Maria da Silva')
    banco = forms.ChoiceField(label='Banco', choices=[('a', 'Banco A'), ('b', 'Banco B')])
    valor = forms.DecimalField(label='Valor (R$)', help_text='Valor bruto oferecido pelo Banco.')
    email = forms.EmailField(label='E-mail', required=False)
    observacoes = forms.CharField(
        label='Observações', required=False, widget=forms.Textarea(attrs={'rows': 3})
    )
    confirmo = forms.BooleanField(label='Confirmo os dados', required=False)
