from decimal import Decimal

import pytest

from bancos.tests.factories import BancoFactory
from beneficios.tests.factories import BeneficioFactory
from propostas import services
from propostas.exceptions import (
    BancoInativo,
    BeneficioInativo,
    CondicoesInvalidas,
    PropostaTravada,
)
from propostas.models import Proposta
from propostas.tests.factories import PropostaFactory, UsuarioFactory

CONDICOES = {
    'valor': Decimal('12000.00'),
    'prazo': 72,
    'parcela': Decimal('300.00'),
    'taxa': Decimal('1.7000'),
}


@pytest.fixture
def usuario(db):
    return UsuarioFactory()


def test_cria_proposta_digitada_com_operador_e_historico(usuario):
    beneficio, banco = BeneficioFactory(), BancoFactory()

    proposta = services.criar_proposta(
        usuario=usuario,
        beneficio=beneficio,
        banco=banco,
        observacoes='Cliente com pressa',
        **CONDICOES,
    )

    proposta.refresh_from_db()
    assert proposta.status == Proposta.Status.DIGITADA
    assert proposta.operador == usuario
    assert proposta.valor == Decimal('12000.00')
    assert proposta.taxa == Decimal('1.7000')
    assert proposta.observacoes == 'Cliente com pressa'
    assert proposta.history.first().history_user == usuario


def test_nao_cria_com_banco_inativo(usuario):
    with pytest.raises(BancoInativo):
        services.criar_proposta(
            usuario=usuario,
            beneficio=BeneficioFactory(),
            banco=BancoFactory(ativo=False),
            **CONDICOES,
        )
    assert not Proposta.objects.exists()


def test_nao_cria_com_beneficio_inativo(usuario):
    with pytest.raises(BeneficioInativo):
        services.criar_proposta(
            usuario=usuario,
            beneficio=BeneficioFactory(ativo=False),
            banco=BancoFactory(),
            **CONDICOES,
        )
    assert not Proposta.objects.exists()


@pytest.mark.parametrize(
    'campo, valor',
    [
        ('valor', Decimal('0')),
        ('prazo', 0),
        ('parcela', Decimal('-1')),
        ('taxa', Decimal('0')),
    ],
)
def test_condicoes_devem_ser_positivas(usuario, campo, valor):
    with pytest.raises(CondicoesInvalidas):
        services.criar_proposta(
            usuario=usuario,
            beneficio=BeneficioFactory(),
            banco=BancoFactory(),
            **{**CONDICOES, campo: valor},
        )


def test_edita_condicoes_enquanto_digitada(usuario):
    proposta = PropostaFactory()
    novo_banco = BancoFactory()

    services.editar_proposta(
        usuario=usuario,
        proposta=proposta,
        beneficio=proposta.beneficio,
        banco=novo_banco,
        observacoes='Ajustada',
        **CONDICOES,
    )

    proposta.refresh_from_db()
    assert proposta.banco == novo_banco
    assert proposta.prazo == 72
    assert proposta.observacoes == 'Ajustada'
    assert proposta.history.first().history_user == usuario


def test_edicao_nao_troca_para_banco_inativo(usuario):
    proposta = PropostaFactory()

    with pytest.raises(BancoInativo):
        services.editar_proposta(
            usuario=usuario,
            proposta=proposta,
            beneficio=proposta.beneficio,
            banco=BancoFactory(ativo=False),
            observacoes='',
            **CONDICOES,
        )


def test_edicao_mantem_banco_que_ficou_inativo(usuario):
    proposta = PropostaFactory()
    proposta.banco.ativo = False
    proposta.banco.save()

    services.editar_proposta(
        usuario=usuario,
        proposta=proposta,
        beneficio=proposta.beneficio,
        banco=proposta.banco,
        observacoes='',
        **CONDICOES,
    )

    proposta.refresh_from_db()
    assert proposta.prazo == 72


def test_condicoes_travadas_fora_de_digitada(usuario):
    proposta = PropostaFactory(status=Proposta.Status.ENVIADA)

    with pytest.raises(PropostaTravada):
        services.editar_proposta(
            usuario=usuario,
            proposta=proposta,
            beneficio=proposta.beneficio,
            banco=proposta.banco,
            observacoes='',
            **CONDICOES,
        )


@pytest.mark.parametrize('status', Proposta.Status.values)
def test_observacoes_editaveis_em_qualquer_etapa(usuario, status):
    proposta = PropostaFactory(status=status, observacoes='antes')

    services.editar_observacoes(usuario=usuario, proposta=proposta, observacoes='depois')

    proposta.refresh_from_db()
    assert proposta.observacoes == 'depois'
    assert proposta.status == status
    assert proposta.history.first().history_user == usuario
