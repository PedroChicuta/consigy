import pytest
from django.contrib.auth import get_user_model

from bancos import selectors, services
from bancos.exceptions import (
    BancoJaAtivo,
    BancoJaInativo,
    CodigoDeBancoDuplicado,
    NomeDeBancoDuplicado,
)
from bancos.models import Banco
from bancos.tests.factories import BancoFactory


@pytest.fixture
def usuario(db):
    return get_user_model().objects.create_user(username='maria', password='x')


def test_criar_banco_nasce_ativo_e_grava_historico(usuario):
    banco = services.criar_banco(usuario=usuario, nome=' Banco Alfa ', codigo='001')

    assert Banco.objects.get(pk=banco.pk).nome == 'Banco Alfa'
    assert banco.ativo
    assert banco.history.first().history_user == usuario


def test_criar_banco_rejeita_nome_duplicado(usuario):
    BancoFactory(nome='Banco Alfa')

    with pytest.raises(NomeDeBancoDuplicado):
        services.criar_banco(usuario=usuario, nome='banco alfa', codigo='999')

    assert Banco.objects.count() == 1


def test_criar_banco_rejeita_codigo_duplicado(usuario):
    BancoFactory(codigo='001')

    with pytest.raises(CodigoDeBancoDuplicado):
        services.criar_banco(usuario=usuario, nome='Outro', codigo='001')

    assert Banco.objects.count() == 1


def test_editar_banco_mantem_proprio_nome_e_codigo(usuario):
    banco = BancoFactory(nome='Banco Alfa', codigo='001')

    services.editar_banco(usuario=usuario, banco=banco, nome='Banco Alfa', codigo='002')

    banco.refresh_from_db()
    assert banco.codigo == '002'
    assert banco.history.count() == 2


def test_editar_banco_rejeita_codigo_de_outro(usuario):
    BancoFactory(codigo='001')
    banco = BancoFactory(codigo='002')

    with pytest.raises(CodigoDeBancoDuplicado):
        services.editar_banco(usuario=usuario, banco=banco, nome=banco.nome, codigo='001')


def test_inativar_e_reativar_banco(usuario):
    banco = BancoFactory()

    services.inativar_banco(usuario=usuario, banco=banco)
    assert not Banco.objects.get(pk=banco.pk).ativo
    with pytest.raises(BancoJaInativo):
        services.inativar_banco(usuario=usuario, banco=banco)

    services.reativar_banco(usuario=usuario, banco=banco)
    assert Banco.objects.get(pk=banco.pk).ativo
    with pytest.raises(BancoJaAtivo):
        services.reativar_banco(usuario=usuario, banco=banco)


def test_banco_inativo_sai_das_escolhas_mas_continua_na_lista(usuario):
    ativo = BancoFactory()
    inativo = BancoFactory()
    services.inativar_banco(usuario=usuario, banco=inativo)

    assert list(selectors.bancos_ativos()) == [ativo]
    assert set(selectors.listar_bancos()) == {ativo, inativo}
