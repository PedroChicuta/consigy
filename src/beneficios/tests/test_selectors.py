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


def test_buscar_beneficios_ativos_por_nome_numero_e_cpf(cliente):
    b1 = BeneficioFactory(cliente=cliente, numero='9876543210', ativo=True)
    c2 = ClienteFactory(nome='Maria Oliveira', cpf='11144477735', ativo=True)
    b2 = BeneficioFactory(cliente=c2, numero='1122334455', ativo=True)

    # Busca por nome do cliente
    assert list(selectors.buscar_beneficios_ativos(busca='José')) == [b1]
    assert list(selectors.buscar_beneficios_ativos(busca='maria')) == [b2]

    # Busca por número do benefício
    assert list(selectors.buscar_beneficios_ativos(busca='987654')) == [b1]
    assert list(selectors.buscar_beneficios_ativos(busca='112233')) == [b2]

    # Busca por CPF (com e sem máscara)
    assert list(selectors.buscar_beneficios_ativos(busca='52998224725')) == [b1]
    assert list(selectors.buscar_beneficios_ativos(busca='529.982.247-25')) == [b1]
    assert list(selectors.buscar_beneficios_ativos(busca='111.444.777-35')) == [b2]


def test_buscar_beneficios_ativos_ignora_inativos(cliente):
    BeneficioFactory(cliente=cliente, numero='1111111111', ativo=False)
    c_inativo = ClienteFactory(nome='Cliente Inativo', cpf='39053344705', ativo=False)
    BeneficioFactory(cliente=c_inativo, numero='2222222222', ativo=True)

    assert list(selectors.buscar_beneficios_ativos(busca='1111111111')) == []
    assert list(selectors.buscar_beneficios_ativos(busca='Inativo')) == []
    assert list(selectors.buscar_beneficios_ativos(busca='2222222222')) == []


def test_buscar_beneficios_ativos_busca_vazia_retorna_vazio(db):
    BeneficioFactory()
    assert list(selectors.buscar_beneficios_ativos(busca='')) == []
    assert list(selectors.buscar_beneficios_ativos(busca='   ')) == []

