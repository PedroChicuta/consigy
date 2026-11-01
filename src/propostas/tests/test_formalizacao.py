from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction

from contratos.models import Contrato
from contratos.tests.factories import ContratoFactory
from propostas import services
from propostas.exceptions import TransicaoInvalida
from propostas.models import Proposta
from propostas.tests.factories import PropostaFactory, UsuarioFactory

CONDICOES = {
    'valor': Decimal('12000.00'),
    'valor_liberado': Decimal('11000.00'),
    'prazo': 72,
    'parcela': Decimal('300.00'),
    'taxa': Decimal('1.7000'),
}


@pytest.fixture
def usuario(db):
    return UsuarioFactory()


def test_formalizar_aprovada_cria_contrato_com_os_valores(usuario):
    proposta = PropostaFactory(status=Proposta.Status.APROVADA, **CONDICOES)

    contrato = services.formalizar_proposta(usuario=usuario, proposta=proposta)

    proposta.refresh_from_db()
    assert proposta.status == Proposta.Status.FORMALIZADA
    assert contrato.proposta == proposta
    assert contrato.valor_liberado == CONDICOES['valor_liberado']
    assert (contrato.valor, contrato.prazo, contrato.parcela, contrato.taxa) == (
        CONDICOES['valor'],
        CONDICOES['prazo'],
        CONDICOES['parcela'],
        CONDICOES['taxa'],
    )
    assert contrato.history.first().history_user == usuario
    assert proposta.history.first().history_user == usuario


@pytest.mark.parametrize(
    'status',
    [
        Proposta.Status.DIGITADA,
        Proposta.Status.ENVIADA,
        Proposta.Status.EM_ANALISE,
        Proposta.Status.FORMALIZADA,
        Proposta.Status.RECUSADA,
        Proposta.Status.CANCELADA,
    ],
)
def test_formalizar_so_a_partir_de_aprovada(usuario, status):
    proposta = PropostaFactory(status=status)

    with pytest.raises(TransicaoInvalida):
        services.formalizar_proposta(usuario=usuario, proposta=proposta)

    assert not Contrato.objects.exists()


def test_formalizar_e_atomico_se_o_contrato_falha(usuario, monkeypatch):
    proposta = PropostaFactory(status=Proposta.Status.APROVADA)

    def falha(**kwargs):
        raise RuntimeError('boom')

    monkeypatch.setattr('propostas.services.criar_contrato', falha)

    with pytest.raises(RuntimeError):
        services.formalizar_proposta(usuario=usuario, proposta=proposta)

    proposta.refresh_from_db()
    assert proposta.status == Proposta.Status.APROVADA
    assert not Contrato.objects.exists()


def test_cada_contrato_tem_uma_proposta_de_origem(db):
    contrato = ContratoFactory()

    with pytest.raises(IntegrityError), transaction.atomic():
        ContratoFactory(proposta=contrato.proposta)
