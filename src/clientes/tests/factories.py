import datetime

import factory

from clientes.models import Cliente

CPFS_VALIDOS = ['52998224725', '11144477735', '39053344705', '12345678909']


class ClienteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Cliente

    nome = factory.Sequence(lambda n: f'Cliente {n}')
    cpf = factory.Iterator(CPFS_VALIDOS)
    data_nascimento = datetime.date(1950, 5, 20)
    telefone = '(11) 99999-0000'
