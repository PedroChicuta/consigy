from datetime import timedelta

import pytest
from django.utils import timezone

from contratos import selectors, services
from contratos.exceptions import DataPagamentoInvalida, MotivoObrigatorio, TransicaoInvalida
from contratos.models import Contrato
from contratos.tests.factories import ContratoFactory
from propostas.tests.factories import UsuarioFactory

S = Contrato.Status


@pytest.mark.django_db
def test_avanca_na_ordem_ate_quitar():
    usuario = UsuarioFactory()
    contrato = ContratoFactory()

    hoje = timezone.localdate()
    for etapa in (S.AVERBADO, S.PAGO, S.QUITADO):
        services.avancar_contrato(
            usuario=usuario, contrato=contrato, status=etapa, data_pagamento=hoje
        )
        contrato.refresh_from_db()
        assert contrato.status == etapa
    assert contrato.data_pagamento == hoje


@pytest.mark.django_db
def test_marcar_pago_sem_data_e_rejeitado():
    contrato = ContratoFactory(status=S.AVERBADO)

    with pytest.raises(DataPagamentoInvalida, match='Informe a data'):
        services.avancar_contrato(usuario=UsuarioFactory(), contrato=contrato, status=S.PAGO)

    contrato.refresh_from_db()
    assert contrato.status == S.AVERBADO


@pytest.mark.django_db
def test_marcar_pago_com_data_futura_e_rejeitado():
    contrato = ContratoFactory(status=S.AVERBADO)
    amanha = timezone.localdate() + timedelta(days=1)

    with pytest.raises(DataPagamentoInvalida, match='futura'):
        services.avancar_contrato(
            usuario=UsuarioFactory(), contrato=contrato, status=S.PAGO, data_pagamento=amanha
        )


@pytest.mark.django_db
def test_marcar_pago_aceita_data_passada():
    contrato = ContratoFactory(status=S.AVERBADO)
    ontem = timezone.localdate() - timedelta(days=1)

    services.avancar_contrato(
        usuario=UsuarioFactory(), contrato=contrato, status=S.PAGO, data_pagamento=ontem
    )

    contrato.refresh_from_db()
    assert contrato.data_pagamento == ontem


@pytest.mark.django_db
def test_filtro_por_periodo_de_pagamento_ignora_sem_data():
    hoje = timezone.localdate()
    dentro = ContratoFactory(status=S.PAGO, data_pagamento=hoje)
    ContratoFactory(status=S.PAGO, data_pagamento=hoje - timedelta(days=30))
    ContratoFactory(status=S.PAGO)  # antigo, sem data

    achados = selectors.listar_contratos(pago_de=hoje - timedelta(days=5), pago_ate=hoje)

    assert list(achados) == [dentro]
    assert selectors.listar_contratos().count() == 3


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
