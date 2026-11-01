from decimal import Decimal

import factory

from contratos.models import Contrato
from propostas.tests.factories import PropostaFactory


class ContratoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contrato

    proposta = factory.SubFactory(PropostaFactory, status='formalizada')
    valor = Decimal('10000.00')
    valor_liberado = Decimal('9000.00')
    prazo = 84
    parcela = Decimal('250.00')
    taxa = Decimal('1.6500')
