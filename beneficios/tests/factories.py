import datetime
from decimal import Decimal

import factory

from beneficios.models import Beneficio, Margem
from clientes.tests.factories import ClienteFactory


class BeneficioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Beneficio

    cliente = factory.SubFactory(ClienteFactory)
    numero = factory.Sequence(lambda n: f'{1000000000 + n}')
    especie = Beneficio.Especie.APOSENTADORIA


class MargemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Margem

    beneficio = factory.SubFactory(BeneficioFactory)
    valor = Decimal('350.00')
    data_consulta = factory.LazyFunction(datetime.date.today)
