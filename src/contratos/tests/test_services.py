import pytest

from contratos import selectors, services
from contratos.exceptions import MotivoObrigatorio, TransicaoInvalida
from contratos.models import Contrato
from contratos.tests.factories import ContratoFactory
from propostas.tests.factories import UsuarioFactory

S = Contrato.Status


@pytest.mark.django_db
def test_avanca_na_ordem_ate_quitar():
    usuario = UsuarioFactory()
    contrato = ContratoFactory()

    for etapa in (S.AVERBADO, S.PAGO, S.QUITADO):
        services.avancar_contrato(usuario=usuario, contrato=contrato, status=etapa)
        contrato.refresh_from_db()
        assert contrato.status == etapa


@pytest.mark.django_db
@pytest.mark.parametrize(
    'atual, destino',
    [
        (S.FORMALIZADO, S.PAGO),
        (S.FORMALIZADO, S.QUITADO),
        (S.AVERBADO, S.QUITADO),
        (S.AVERBADO, S.AVERBADO),
        (S.PAGO, S.AVERBADO),
        (S.QUITADO, S.PAGO),
        (S.CANCELADO, S.AVERBADO),
        (S.FORMALIZADO, S.CANCELADO),
        (S.FORMALIZADO, 'qualquer'),
    ],
)
def test_nao_pula_nem_volta_etapa(atual, destino):
    contrato = ContratoFactory(status=atual)

    with pytest.raises(TransicaoInvalida):
        services.avancar_contrato(usuario=UsuarioFactory(), contrato=contrato, status=destino)

    contrato.refresh_from_db()
    assert contrato.status == atual


@pytest.mark.django_db
@pytest.mark.parametrize('atual', [S.FORMALIZADO, S.AVERBADO])
def test_cancela_quando_averbacao_ou_pagamento_falha(atual):
    contrato = ContratoFactory(status=atual)

    services.cancelar_contrato(usuario=UsuarioFactory(), contrato=contrato, motivo=' INSS negou ')

    contrato.refresh_from_db()
    assert contrato.status == S.CANCELADO
    assert contrato.motivo == 'INSS negou'


@pytest.mark.django_db
@pytest.mark.parametrize('motivo', ['', '   ', None])
def test_cancelar_exige_motivo(motivo):
    contrato = ContratoFactory()

    with pytest.raises(MotivoObrigatorio):
        services.cancelar_contrato(usuario=UsuarioFactory(), contrato=contrato, motivo=motivo)

    contrato.refresh_from_db()
    assert contrato.status == S.FORMALIZADO


@pytest.mark.django_db
@pytest.mark.parametrize('final', [S.PAGO, S.QUITADO, S.CANCELADO])
def test_cancelar_nao_vale_depois_do_pagamento_nem_reabre(final):
    contrato = ContratoFactory(status=final)

    with pytest.raises(TransicaoInvalida):
        services.cancelar_contrato(usuario=UsuarioFactory(), contrato=contrato, motivo='x')

    contrato.refresh_from_db()
    assert contrato.status == final


@pytest.mark.django_db
def test_historico_registra_autor_de_cada_mudanca_de_status():
    autor = UsuarioFactory()
    contrato = ContratoFactory()
    services.avancar_contrato(usuario=autor, contrato=contrato, status=S.AVERBADO)

    historico = selectors.historico_do_contrato(contrato=contrato)

    assert [r.status for r in historico][0] == S.AVERBADO
    assert historico[0].history_user == autor
