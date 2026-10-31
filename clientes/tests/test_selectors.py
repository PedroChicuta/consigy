import pytest

from clientes import selectors
from clientes.tests.factories import ClienteFactory


@pytest.fixture
def clientes(db):
    return (
        ClienteFactory(nome='José da Silva', cpf='52998224725'),
        ClienteFactory(nome='Maria Souza', cpf='11144477735'),
    )


@pytest.mark.parametrize('busca', ['52998224725', '529.982.247-25', '529982247', '982.247'])
def test_busca_por_cpf_com_ou_sem_mascara(clientes, busca):
    assert list(selectors.listar_clientes(busca=busca)) == [clientes[0]]


@pytest.mark.parametrize('busca', ['silva', 'José DA', ' Silva '])
def test_busca_por_parte_do_nome(clientes, busca):
    assert list(selectors.listar_clientes(busca=busca)) == [clientes[0]]


def test_busca_vazia_devolve_todos(clientes):
    assert selectors.listar_clientes(busca='').count() == 2
    assert selectors.listar_clientes().count() == 2


def test_busca_sem_resultado(clientes):
    assert not selectors.listar_clientes(busca='zzz').exists()


def test_nome_com_numero_nao_vira_busca_por_cpf(clientes):
    assert not selectors.listar_clientes(busca='Silva 1').exists()
