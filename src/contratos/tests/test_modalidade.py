import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.urls import reverse

from contratos import selectors
from contratos.models import Contrato
from contratos.tests.factories import ContratoFactory
from propostas import selectors as propostas_selectors
from propostas.models import Proposta
from propostas.tests.factories import ModalidadeFactory, PropostaFactory


@pytest.fixture
def operador(client, db):
    usuario = get_user_model().objects.create_user(username='operador', password='x')
    usuario.groups.add(Group.objects.get(name='Operador'))
    client.force_login(usuario)
    return usuario


def test_contrato_copia_a_modalidade_da_proposta(client, operador):
    modalidade = ModalidadeFactory(nome='Portabilidade X', envolve_portabilidade=True)
    proposta = PropostaFactory(status=Proposta.Status.APROVADA, modalidade=modalidade)

    client.post(reverse('propostas:formalizar', args=[proposta.pk]))

    assert Contrato.objects.get().modalidade == modalidade


def test_modalidade_aparece_na_lista_e_no_detalhe(client, operador):
    contrato = ContratoFactory(proposta__modalidade=ModalidadeFactory(nome='Cartão Y'))

    lista = client.get(reverse('contratos:lista'))
    detalhe = client.get(reverse('contratos:detalhe', args=[contrato.pk]))

    assert 'Cartão Y' in lista.content.decode()
    assert 'Cartão Y' in detalhe.content.decode()


def test_filtro_de_contratos_por_modalidade_combina_com_status(db):
    a, b = ModalidadeFactory(), ModalidadeFactory()
    alvo = ContratoFactory(proposta__modalidade=a, status=Contrato.Status.AVERBADO)
    ContratoFactory(proposta__modalidade=a, status=Contrato.Status.FORMALIZADO)
    ContratoFactory(proposta__modalidade=b, status=Contrato.Status.AVERBADO)

    assert selectors.listar_contratos(modalidade=a.pk).count() == 2
    resultado = selectors.listar_contratos(modalidade=a.pk, status=Contrato.Status.AVERBADO)
    assert list(resultado) == [alvo]


def test_filtro_de_contratos_por_modalidade_inativa_funciona(client, operador):
    inativa = ModalidadeFactory(ativo=False)
    contrato = ContratoFactory(proposta__modalidade=inativa)
    ContratoFactory()

    resposta = client.get(reverse('contratos:lista'), {'modalidade': inativa.pk})

    assert list(resposta.context['pagina']) == [contrato]


def test_filtro_de_propostas_por_modalidade_combina_com_status(client, operador):
    a, b = ModalidadeFactory(), ModalidadeFactory(ativo=False)
    alvo = PropostaFactory(modalidade=b, status=Proposta.Status.ENVIADA)
    PropostaFactory(modalidade=b, status=Proposta.Status.DIGITADA)
    PropostaFactory(modalidade=a, status=Proposta.Status.ENVIADA)

    resposta = client.get(
        reverse('propostas:lista'), {'modalidade': b.pk, 'status': Proposta.Status.ENVIADA}
    )

    assert list(resposta.context['pagina']) == [alvo]
    assert list(propostas_selectors.listar_propostas(modalidade=b.pk)).count(alvo) == 1


def test_nao_ha_migrations_pendentes(db):
    call_command('makemigrations', '--check', '--dry-run', verbosity=0)


ANTES = [
    ('propostas', '0008_valor_liberado'),
    ('contratos', '0006_contrato_data_pagamento_and_more'),
]
DEPOIS = [('contratos', '0007_modalidade')]


@pytest.mark.django_db(transaction=True)
def test_migration_liga_contratos_antigos_a_modalidade_da_proposta():
    executor = MigrationExecutor(connection)
    executor.migrate(ANTES)
    try:
        apps = executor.loader.project_state(ANTES).apps
        Modalidade = apps.get_model('propostas', 'Modalidade')
        novo = Modalidade.objects.get(nome='Consignado novo')
        usuario = apps.get_model('accounts', 'User').objects.create(username='antigo')
        Banco = apps.get_model('bancos', 'Banco')
        cliente = apps.get_model('clientes', 'Cliente').objects.create(
            nome='Fulano',
            cpf='52998224725',
            data_nascimento='1960-01-01',
            telefone='11999999999',
        )
        beneficio = apps.get_model('beneficios', 'Beneficio').objects.create(
            cliente=cliente, numero='1234567890', especie='aposentadoria'
        )
        banco = Banco.objects.create(nome='Banco A', codigo='001')
        proposta = apps.get_model('propostas', 'Proposta').objects.create(
            beneficio=beneficio,
            banco=banco,
            modalidade=novo,
            operador=usuario,
            valor=1,
            valor_liberado=1,
            prazo=12,
            parcela=1,
            taxa=1,
        )
        contrato = apps.get_model('contratos', 'Contrato').objects.create(
            proposta=proposta, valor=1, valor_liberado=1, prazo=12, parcela=1, taxa=1
        )

        executor = MigrationExecutor(connection)
        executor.migrate(DEPOIS)
        apps = executor.loader.project_state(DEPOIS).apps
        migrado = apps.get_model('contratos', 'Contrato').objects.get(pk=contrato.pk)
        assert migrado.modalidade.nome == 'Consignado novo'
    finally:
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
