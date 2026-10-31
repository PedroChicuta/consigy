import datetime

from django.db import models
from simple_history.models import HistoricalRecords

from clientes.models import Cliente

# Depois disso, a Margem consultada pede nova consulta.
DIAS_MARGEM_ANTIGA = 30


class Beneficio(models.Model):
    """Aposentadoria ou pensão do INSS de um Cliente."""

    class Especie(models.TextChoices):
        APOSENTADORIA = 'aposentadoria', 'Aposentadoria'
        PENSAO = 'pensao', 'Pensão'

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='beneficios')
    numero = models.CharField('número', max_length=20, unique=True)
    especie = models.CharField('espécie', max_length=20, choices=Especie)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['numero']
        verbose_name = 'benefício'

    def __str__(self):
        return self.numero


class Margem(models.Model):
    """Margem consignável de um Benefício, digitada com a data da consulta."""

    beneficio = models.ForeignKey(Beneficio, on_delete=models.PROTECT, related_name='margens')
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_consulta = models.DateField('data da consulta')
    criado_em = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['-data_consulta', '-pk']
        verbose_name_plural = 'margens'

    def __str__(self):
        return f'{self.valor} em {self.data_consulta:%d/%m/%Y}'

    @property
    def antiga(self):
        return (datetime.date.today() - self.data_consulta).days > DIAS_MARGEM_ANTIGA
