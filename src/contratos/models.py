from django.db import models
from simple_history.models import HistoricalRecords

from propostas.models import Proposta


class Contrato(models.Model):
    """Empréstimo efetivado, nascido de uma única Proposta Formalizada."""

    class Status(models.TextChoices):
        FORMALIZADO = 'formalizado', 'Aguardando averbação'
        AVERBADO = 'averbado', 'Averbado'
        PAGO = 'pago', 'Pago'
        QUITADO = 'quitado', 'Quitado'
        CANCELADO = 'cancelado', 'Cancelado'

    proposta = models.OneToOneField(Proposta, on_delete=models.PROTECT, related_name='contrato')
    status = models.CharField(max_length=20, choices=Status, default=Status.FORMALIZADO)
    valor = models.DecimalField('valor (R$)', max_digits=12, decimal_places=2)
    valor_liberado = models.DecimalField('valor liberado (R$)', max_digits=12, decimal_places=2)
    prazo = models.PositiveSmallIntegerField('prazo (meses)')
    parcela = models.DecimalField('parcela (R$)', max_digits=10, decimal_places=2)
    taxa = models.DecimalField('taxa (% a.m.)', max_digits=6, decimal_places=4)
    data_pagamento = models.DateField('data de pagamento', null=True, blank=True)
    motivo = models.TextField('motivo do cancelamento', blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['-criado_em', '-pk']

    def __str__(self):
        return f'Contrato {self.pk}'

    @property
    def cliente(self):
        return self.proposta.beneficio.cliente
