import pytest

from bancos.tests.factories import BancoFactory
from beneficios.tests.factories import BeneficioFactory
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
