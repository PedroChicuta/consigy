import factory
from django.contrib.auth import get_user_model


class UsuarioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: f'operador{n}')


def test_factory_boy_cria_usuario(db):
    usuario = UsuarioFactory()

    assert usuario.pk is not None
    assert usuario.username.startswith('operador')
