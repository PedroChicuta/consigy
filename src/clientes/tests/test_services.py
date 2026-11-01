import datetime

import pytest
from django.contrib.auth import get_user_model

from clientes import services
from clientes.cpf import cpf_valido
from clientes.exceptions import ClienteJaAtivo, ClienteJaInativo, CpfDuplicado, CpfInvalido
from clientes.models import Cliente
from clientes.tests.factories import ClienteFactory

DADOS = {
    'nome': 'José da Silva',
    'cpf': '529.982.247-25',
    'data_nascimento': datetime.date(1948, 3, 2),
    'telefone': '(11) 98888-7777',
}


@pytest.fixture
def usuario(db):
    return get_user_model().objects.create_user(username='maria', password='x')


def test_cpf_valido_pelos_digitos_verificadores():
    assert cpf_valido('52998224725')
    assert not cpf_valido('52998224726')
    assert not cpf_valido('11111111111')
    assert not cpf_valido('123')


def test_criar_cliente_guarda_cpf_so_com_digitos(usuario):
    cliente = services.criar_cliente(usuario=usuario, **DADOS)

    assert Cliente.objects.get(pk=cliente.pk).cpf == '52998224725'
    assert cliente.ativo


def test_criar_cliente_aceita_cpf_sem_mascara(usuario):
    cliente = services.criar_cliente(usuario=usuario, **{**DADOS, 'cpf': '52998224725'})

    assert cliente.cpf == '52998224725'


def test_cpf_invalido_e_recusado_e_nada_e_gravado(usuario):
    with pytest.raises(CpfInvalido):
        services.criar_cliente(usuario=usuario, **{**DADOS, 'cpf': '529.982.247-26'})

    assert not Cliente.objects.exists()


def test_cpf_duplicado_aponta_o_cliente_existente(usuario):
    existente = services.criar_cliente(usuario=usuario, **DADOS)

    with pytest.raises(CpfDuplicado) as erro:
        services.criar_cliente(usuario=usuario, **{**DADOS, 'cpf': '52998224725'})

    assert erro.value.cliente == existente
    assert Cliente.objects.count() == 1


def test_editar_cliente_muda_nome_e_contato(usuario):
    cliente = ClienteFactory()

    services.editar_cliente(
        usuario=usuario, cliente=cliente, nome='Novo Nome', telefone='1', email='a@b.com'
    )

    cliente.refresh_from_db()
    assert (cliente.nome, cliente.telefone, cliente.email) == ('Novo Nome', '1', 'a@b.com')


def test_inativar_e_reativar(usuario):
    cliente = ClienteFactory()

    services.inativar_cliente(usuario=usuario, cliente=cliente)
    cliente.refresh_from_db()
    assert not cliente.ativo
    with pytest.raises(ClienteJaInativo):
        services.inativar_cliente(usuario=usuario, cliente=cliente)

    services.reativar_cliente(usuario=usuario, cliente=cliente)
    cliente.refresh_from_db()
    assert cliente.ativo
    with pytest.raises(ClienteJaAtivo):
        services.reativar_cliente(usuario=usuario, cliente=cliente)


def test_historico_registra_autor_de_cada_alteracao(usuario):
    cliente = services.criar_cliente(usuario=usuario, **DADOS)
    services.editar_cliente(usuario=usuario, cliente=cliente, nome='Outro', telefone='2')
    services.inativar_cliente(usuario=usuario, cliente=cliente)

    registros = list(cliente.history.order_by('history_date', 'pk'))

    assert [r.history_type for r in registros] == ['+', '~', '~']
    assert all(r.history_user == usuario for r in registros)
