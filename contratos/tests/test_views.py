import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from contratos.models import Contrato
from propostas.models import Proposta
from propostas.tests.factories import PropostaFactory


@pytest.fixture
def operador(client, db):
    usuario = get_user_model().objects.create_user(username='operador', password='x')
    usuario.groups.add(Group.objects.get(name='Operador'))
    client.force_login(usuario)
    return usuario


def test_operador_formaliza_e_ve_o_contrato_nas_fichas(client, operador):
    proposta = PropostaFactory(status=Proposta.Status.APROVADA)

    resposta = client.post(reverse('propostas:formalizar', args=[proposta.pk]))

    assert resposta.status_code == 302
    contrato = Contrato.objects.get()
    assert contrato.proposta == proposta
    ficha_proposta = client.get(reverse('propostas:detalhe', args=[proposta.pk]))
    assert f'<td>{contrato.pk}</td>' in ficha_proposta.content.decode()
    ficha_cliente = client.get(reverse('clientes:detalhe', args=[proposta.cliente.pk]))
    assert f'<td>{contrato.pk}</td>' in ficha_cliente.content.decode()


def test_formalizar_proposta_nao_aprovada_nao_cria_contrato(client, operador):
    proposta = PropostaFactory(status=Proposta.Status.EM_ANALISE)

    client.post(reverse('propostas:formalizar', args=[proposta.pk]))

    proposta.refresh_from_db()
    assert proposta.status == Proposta.Status.EM_ANALISE
    assert not Contrato.objects.exists()


def test_sem_permissao_nao_formaliza(client, db):
    client.force_login(get_user_model().objects.create_user(username='sem', password='x'))
    proposta = PropostaFactory(status=Proposta.Status.APROVADA)

    resposta = client.post(reverse('propostas:formalizar', args=[proposta.pk]))

    assert resposta.status_code == 403
    assert not Contrato.objects.exists()
