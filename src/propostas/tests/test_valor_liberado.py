from decimal import Decimal

import pytest
from django.contrib.auth.models import Group
from django.urls import reverse

from contratos.tests.factories import ContratoFactory
from propostas.tests.factories import PropostaFactory, UsuarioFactory


@pytest.fixture
def operador(client, db):
    usuario = UsuarioFactory()
    usuario.groups.add(Group.objects.get(name='Operador'))
    client.force_login(usuario)
    return usuario


def test_listas_e_detalhes_mostram_valor_liberado(client, operador):
    proposta = PropostaFactory(valor_liberado=Decimal('8123.45'))
    contrato = ContratoFactory(valor_liberado=Decimal('7654.32'))

    assert '8123,45' in client.get(reverse('propostas:lista')).content.decode()
    assert (
        '8123,45' in client.get(reverse('propostas:detalhe', args=[proposta.pk])).content.decode()
    )
    assert '7654,32' in client.get(reverse('contratos:lista')).content.decode()
    assert (
        '7654,32' in client.get(reverse('contratos:detalhe', args=[contrato.pk])).content.decode()
    )
