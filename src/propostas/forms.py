from django import forms
from django.db.models import Q

from bancos.models import Banco
from beneficios.models import Beneficio
from propostas import selectors
from propostas.models import Modalidade


class PropostaForm(forms.Form):
    beneficio = forms.ModelChoiceField(
        queryset=Beneficio.objects.none(),
        widget=forms.HiddenInput(),
        error_messages={'required': 'Selecione um Benefício.'},
    )
    banco = forms.ModelChoiceField(
        queryset=Banco.objects.none(), label='Banco', empty_label='Selecione o Banco'
    )
    modalidade = forms.ModelChoiceField(
        queryset=Modalidade.objects.none(),
        label='Modalidade',
        empty_label='Selecione a Modalidade',
    )
    valor = forms.DecimalField(label='Valor (R$)', max_digits=12, decimal_places=2)
    valor_liberado = forms.DecimalField(
        label='Valor liberado (R$)', max_digits=12, decimal_places=2
    )
    prazo = forms.IntegerField(label='Prazo (meses)', min_value=1, max_value=32767)
    parcela = forms.DecimalField(label='Parcela (R$)', max_digits=10, decimal_places=2)
    taxa = forms.DecimalField(label='Taxa (% a.m.)', max_digits=6, decimal_places=4)
    observacoes = forms.CharField(
        label='Observações', required=False, widget=forms.Textarea(attrs={'rows': 3})
    )

    def __init__(self, *args, proposta=None, **kwargs):
        super().__init__(*args, **kwargs)
        filtro_beneficio, filtro_banco = Q(ativo=True, cliente__ativo=True), Q(ativo=True)
        if proposta is not None:
            # Mantém a escolha atual, mesmo que tenha sido inativada depois da digitação.
            filtro_beneficio = Q(ativo=True, cliente__ativo=True) | Q(pk=proposta.beneficio_id)
            filtro_banco |= Q(pk=proposta.banco_id)
            modalidades = Modalidade.objects.filter(Q(ativo=True) | Q(pk=proposta.modalidade_id))
        else:
            modalidades = selectors.modalidades_ativas()
        self.fields['beneficio'].queryset = Beneficio.objects.select_related('cliente').filter(
            filtro_beneficio
        )
        self.fields['banco'].queryset = Banco.objects.filter(filtro_banco)
        self.fields['modalidade'].queryset = modalidades


class ObservacoesForm(forms.Form):
    observacoes = forms.CharField(
        label='Observações',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
    )


class MotivoForm(forms.Form):
    motivo = forms.CharField(label='Motivo')


class ModalidadeForm(forms.Form):
    nome = forms.CharField(label='Nome', max_length=100)
    envolve_portabilidade = forms.BooleanField(label='Envolve portabilidade', required=False)
