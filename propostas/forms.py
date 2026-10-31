from django import forms
from django.db.models import Q

from bancos.models import Banco
from beneficios.models import Beneficio


class _BeneficioChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{obj.numero} · {obj.cliente.nome}'


class PropostaForm(forms.Form):
    beneficio = _BeneficioChoiceField(queryset=Beneficio.objects.none(), label='Benefício')
    banco = forms.ModelChoiceField(queryset=Banco.objects.none(), label='Banco')
    valor = forms.DecimalField(label='Valor (R$)', max_digits=12, decimal_places=2)
    prazo = forms.IntegerField(label='Prazo (meses)', min_value=1, max_value=32767)
    parcela = forms.DecimalField(label='Parcela (R$)', max_digits=10, decimal_places=2)
    taxa = forms.DecimalField(label='Taxa (% a.m.)', max_digits=6, decimal_places=4)
    observacoes = forms.CharField(
        label='Observações', required=False, widget=forms.Textarea(attrs={'rows': 3})
    )

    def __init__(self, *args, proposta=None, **kwargs):
        super().__init__(*args, **kwargs)
        filtro_beneficio, filtro_banco = Q(ativo=True), Q(ativo=True)
        if proposta is not None:
            # Mantém a escolha atual, mesmo que tenha sido inativada depois da digitação.
            filtro_beneficio |= Q(pk=proposta.beneficio_id)
            filtro_banco |= Q(pk=proposta.banco_id)
        self.fields['beneficio'].queryset = Beneficio.objects.select_related('cliente').filter(
            filtro_beneficio
        )
        self.fields['banco'].queryset = Banco.objects.filter(filtro_banco)
        for nome, campo in self.fields.items():
            campo.widget.attrs['class'] = (
                'form-select' if nome in ('beneficio', 'banco') else 'form-control'
            )


class ObservacoesForm(forms.Form):
    observacoes = forms.CharField(
        label='Observações',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
    )
