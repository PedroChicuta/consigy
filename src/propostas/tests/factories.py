from decimal import Decimal

import factory
from django.contrib.auth import get_user_model

from bancos.tests.factories import BancoFactory
from beneficios.tests.factories import BeneficioFactory
from propostas.models import Proposta


class UsuarioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: f'operador{n}')


class PropostaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Proposta

    beneficio = factory.SubFactory(BeneficioFactory)
    banco = factory.SubFactory(BancoFactory)
    operador = factory.SubFactory(UsuarioFactory)
    valor = Decimal('10000.00')
    prazo = 84
    parcela = Decimal('250.00')
    taxa = Decimal('1.6500')
