from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords

from bancos.models import Banco
from beneficios.models import Beneficio


class Modalidade(models.Model):
    """Tipo de operação de crédito de uma Proposta; cadastro mantido pelo Supervisor no admin."""

    nome = models.CharField(max_length=100, unique=True)
    ativo = models.BooleanField(default=True)
    envolve_portabilidade = models.BooleanField('envolve portabilidade', default=False)

    history = HistoricalRecords()

    class Meta:
        ordering = ['nome']
        verbose_name_plural = 'modalidades'

    def __str__(self):
        return self.nome


class Proposta(models.Model):
    """Pedido de empréstimo consignado novo, feito sobre um Benefício e enviado a um Banco."""

    class Status(models.TextChoices):
        DIGITADA = 'digitada', 'Digitada'
        ENVIADA = 'enviada', 'Enviada ao Banco'
        EM_ANALISE = 'em_analise', 'Em análise'
        APROVADA = 'aprovada', 'Aprovada'
        FORMALIZADA = 'formalizada', 'Formalizada'
        RECUSADA = 'recusada', 'Recusada'
        CANCELADA = 'cancelada', 'Cancelada'

    beneficio = models.ForeignKey(Beneficio, on_delete=models.PROTECT, related_name='propostas')
    banco = models.ForeignKey(Banco, on_delete=models.PROTECT, related_name='propostas')
    modalidade = models.ForeignKey(Modalidade, on_delete=models.PROTECT, related_name='propostas')
    operador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='propostas'
    )
    status = models.CharField(max_length=20, choices=Status, default=Status.DIGITADA)
    valor = models.DecimalField('valor (R$)', max_digits=12, decimal_places=2)
    valor_liberado = models.DecimalField('valor liberado (R$)', max_digits=12, decimal_places=2)
    prazo = models.PositiveSmallIntegerField('prazo (meses)')
    parcela = models.DecimalField('parcela (R$)', max_digits=10, decimal_places=2)
    taxa = models.DecimalField('taxa (% a.m.)', max_digits=6, decimal_places=4)
    observacoes = models.TextField('observações', blank=True)
    motivo = models.TextField('motivo do encerramento', blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['-criado_em', '-pk']
        permissions = [
            ('cancelar_proposta_aprovada', 'Pode cancelar uma Proposta Aprovada'),
        ]

    def __str__(self):
        return f'Proposta {self.pk}'

    @property
    def cliente(self):
        return self.beneficio.cliente


FINAIS = {Proposta.Status.FORMALIZADA, Proposta.Status.RECUSADA, Proposta.Status.CANCELADA}
