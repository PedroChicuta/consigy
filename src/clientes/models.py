from django.db import models
from simple_history.models import HistoricalRecords

from clientes.cpf import formatar_cpf, mascarar_cpf


class Cliente(models.Model):
    """Pessoa física, aposentada ou pensionista do INSS, identificada por um CPF único."""

    nome = models.CharField(max_length=150)
    cpf = models.CharField('CPF', max_length=11, unique=True)
    data_nascimento = models.DateField('data de nascimento')
    telefone = models.CharField(max_length=20)
    email = models.EmailField('e-mail', blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome

    @property
    def cpf_formatado(self):
        return formatar_cpf(self.cpf)

    @property
    def cpf_mascarado(self):
        return mascarar_cpf(self.cpf)
