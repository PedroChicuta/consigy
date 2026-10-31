from django.db import models
from simple_history.models import HistoricalRecords


class Banco(models.Model):
    """Instituição financeira que analisa a Proposta e paga o Contrato."""

    nome = models.CharField(max_length=100, unique=True)
    codigo = models.CharField('código', max_length=10, unique=True)
    ativo = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome
