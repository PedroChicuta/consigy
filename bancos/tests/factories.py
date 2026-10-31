import factory

from bancos.models import Banco


class BancoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Banco

    nome = factory.Sequence(lambda n: f'Banco {n}')
    codigo = factory.Sequence(lambda n: f'{n:03d}')
