import datetime

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from bancos.tests.factories import BancoFactory
from beneficios.tests.factories import BeneficioFactory, MargemFactory
from propostas.models import Proposta
from propostas.tests.factories import PropostaFactory

DADOS = {'valor': '9000.00', 'prazo': '60', 'parcela': '200.00', 'taxa': '1.5000'}


@pytest.fixture
def operador(client, db):
    usuario = get_user_model().objects.create_user(username='operador', password='x')
    usuario.groups.add(Group.objects.get(name='Operador'))
    client.force_login(usuario)
    return usuario


def test_sem_permissao_e_barrado(client, db):
    client.force_login(get_user_model().objects.create_user(username='sem', password='x'))

    assert client.get(reverse('propostas:lista')).status_code == 403
    assert client.get(reverse('propostas:criar')).status_code == 403


def test_operador_cria_proposta(client, operador):
    beneficio, banco = BeneficioFactory(), BancoFactory()

    resposta = client.post(
        reverse('propostas:criar'), {**DADOS, 'beneficio': beneficio.pk, 'banco': banco.pk}
    )

    proposta = Proposta.objects.get()
    assert resposta.status_code == 302
    assert resposta.url == reverse('propostas:detalhe', args=[proposta.pk])
    assert proposta.operador == operador


def test_banco_inativo_volta_com_erro(client, operador):
    beneficio, banco = BeneficioFactory(), BancoFactory(ativo=False)

    resposta = client.post(
        reverse('propostas:criar'), {**DADOS, 'beneficio': beneficio.pk, 'banco': banco.pk}
    )

    assert resposta.status_code == 200
    assert not Proposta.objects.exists()


def test_lista_filtra_e_responde_fragmento_via_htmx(client, operador):
    banco = BancoFactory(nome='Banco Alvo')
    PropostaFactory(banco=banco)
    PropostaFactory(banco=BancoFactory(nome='Banco Outro'))

    resposta = client.get(
        reverse('propostas:lista'), {'banco': banco.pk}, headers={'HX-Request': 'true'}
    )

    conteudo = resposta.content.decode()
    assert 'Banco Alvo' in conteudo
    assert 'Banco Outro' not in conteudo
    assert '<html' not in conteudo


def test_lista_ignora_filtros_invalidos(client, operador):
    PropostaFactory()

    resposta = client.get(reverse('propostas:lista'), {'banco': 'x', 'status': 'y'})

    assert resposta.status_code == 200


def test_operador_edita_condicoes_e_observacoes(client, operador):
    proposta = PropostaFactory()

    resposta = client.post(
        reverse('propostas:editar', args=[proposta.pk]),
        {**DADOS, 'beneficio': proposta.beneficio_id, 'banco': proposta.banco_id},
    )
    client.post(reverse('propostas:observacoes', args=[proposta.pk]), {'observacoes': 'Nota'})

    proposta.refresh_from_db()
    assert resposta.status_code == 302
    assert proposta.prazo == 60
    assert proposta.observacoes == 'Nota'


def test_operador_envia_proposta(client, operador):
    proposta = PropostaFactory()
    MargemFactory(beneficio=proposta.beneficio)

    resposta = client.post(reverse('propostas:enviar', args=[proposta.pk]))

    proposta.refresh_from_db()
    assert resposta.status_code == 302
    assert proposta.status == Proposta.Status.ENVIADA


def test_envio_com_margem_antiga_pede_confirmacao(client, operador):
    proposta = PropostaFactory()
    MargemFactory(
        beneficio=proposta.beneficio,
        data_consulta=datetime.date.today() - datetime.timedelta(days=45),
    )
    url = reverse('propostas:enviar', args=[proposta.pk])

    resposta = client.post(url)
    assert resposta.status_code == 200
    assert Proposta.objects.get().status == Proposta.Status.DIGITADA

    client.post(url, {'confirmar_margem_antiga': '1'})
    assert Proposta.objects.get().status == Proposta.Status.ENVIADA


def test_ficha_do_cliente_mostra_propostas(client, operador):
    proposta = PropostaFactory()

    resposta = client.get(reverse('clientes:detalhe', args=[proposta.cliente.pk]))

    assert reverse('propostas:detalhe', args=[proposta.pk]) in resposta.content.decode()
