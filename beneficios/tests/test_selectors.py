import pytest

from beneficios import selectors
from beneficios.tests.factories import BeneficioFactory
from clientes import selectors as clientes_selectors
from clientes.tests.factories import ClienteFactory


@pytest.fixture
def cliente(db):
    return ClienteFactory(nome='José da Silva', cpf='52998224725')


def test_clientes_sao_encontrados_pelo_numero_do_beneficio(cliente):
    BeneficioFactory(cliente=cliente, numero='1234567890')
    BeneficioFactory(cliente=ClienteFactory(cpf='11144477735'), numero='9999999999')

    assert list(clientes_selectors.listar_clientes(busca='1234567890')) == [cliente]
    assert list(clientes_selectors.listar_clientes(busca='345678')) == [cliente]


def test_cliente_com_varios_beneficios_aparece_uma_vez(cliente):
    BeneficioFactory(cliente=cliente, numero='1111111111')
    BeneficioFactory(cliente=cliente, numero='1111111112')

    assert clientes_selectors.listar_clientes(busca='111111').count() == 1


def test_beneficios_do_cliente(cliente):
    b = BeneficioFactory(cliente=cliente)
    BeneficioFactory(cliente=ClienteFactory(cpf='39053344705'))

    assert list(selectors.beneficios_do_cliente(cliente=cliente)) == [b]
