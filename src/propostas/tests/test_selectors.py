import datetime
from decimal import Decimal

import pytest

from bancos.tests.factories import BancoFactory
from beneficios.tests.factories import BeneficioFactory, MargemFactory
from clientes.tests.factories import ClienteFactory
from propostas import selectors
from propostas.models import Proposta
from propostas.tests.factories import PropostaFactory


@pytest.mark.django_db
def test_lista_todas_sem_filtro():
    a, b = PropostaFactory(), PropostaFactory()

    assert set(selectors.listar_propostas()) == {a, b}


@pytest.mark.django_db
def test_filtra_por_status():
    digitada = PropostaFactory()
    PropostaFactory(status=Proposta.Status.ENVIADA)

    assert list(selectors.listar_propostas(status='digitada')) == [digitada]


@pytest.mark.django_db
def test_filtra_por_banco():
    banco = BancoFactory()
    do_banco = PropostaFactory(banco=banco)
    PropostaFactory()

    assert list(selectors.listar_propostas(banco=banco.pk)) == [do_banco]


@pytest.mark.django_db
def test_filtra_por_cliente_pelo_nome_ou_cpf():
    cliente = ClienteFactory(nome='Maria Aparecida')
    do_cliente = PropostaFactory(beneficio=BeneficioFactory(cliente=cliente))
    PropostaFactory()

    assert list(selectors.listar_propostas(cliente='aparecida')) == [do_cliente]
    assert list(selectors.listar_propostas(cliente=cliente.cpf)) == [do_cliente]


@pytest.mark.django_db
def test_filtros_combinam():
    banco = BancoFactory()
    alvo = PropostaFactory(banco=banco)
    PropostaFactory(banco=banco, status=Proposta.Status.ENVIADA)
    PropostaFactory(status=Proposta.Status.DIGITADA)

    resultado = selectors.listar_propostas(status='digitada', banco=banco.pk)

    assert list(resultado) == [alvo]


@pytest.mark.django_db
def test_propostas_do_cliente():
    cliente = ClienteFactory()
    minha = PropostaFactory(beneficio=BeneficioFactory(cliente=cliente))
    PropostaFactory()

    assert list(selectors.propostas_do_cliente(cliente=cliente)) == [minha]


@pytest.mark.django_db
def test_impedimento_sem_margem():
    proposta = PropostaFactory()

    impedimento = selectors.impedimento_envio(proposta=proposta)

    assert impedimento is not None
    assert impedimento['tipo'] == 'sem_margem'
    assert 'não possui Margem' in impedimento['mensagem']


@pytest.mark.django_db
def test_impedimento_parcela_acima_da_margem():
    proposta = PropostaFactory(parcela=Decimal('500.00'))
    MargemFactory(beneficio=proposta.beneficio, valor=Decimal('350.00'))

    impedimento = selectors.impedimento_envio(proposta=proposta)

    assert impedimento is not None
    assert impedimento['tipo'] == 'parcela_acima_da_margem'
    assert 'R$ 500,00' in impedimento['mensagem']
    assert 'R$ 350,00' in impedimento['mensagem']


@pytest.mark.django_db
def test_impedimento_margem_antiga():
    proposta = PropostaFactory(parcela=Decimal('200.00'))
    MargemFactory(
        beneficio=proposta.beneficio,
        valor=Decimal('500.00'),
        data_consulta=datetime.date.today() - datetime.timedelta(days=35),
    )

    impedimento = selectors.impedimento_envio(proposta=proposta)

    assert impedimento is not None
    assert impedimento['tipo'] == 'margem_antiga'
    assert 'mais de 30 dias' in impedimento['mensagem']


@pytest.mark.django_db
def test_sem_impedimento_quando_valida():
    proposta = PropostaFactory(parcela=Decimal('200.00'))
    MargemFactory(beneficio=proposta.beneficio, valor=Decimal('500.00'))

    assert selectors.impedimento_envio(proposta=proposta) is None


@pytest.mark.django_db
def test_sem_impedimento_para_proposta_nao_digitada():
    proposta = PropostaFactory(status=Proposta.Status.ENVIADA)

    assert selectors.impedimento_envio(proposta=proposta) is None

