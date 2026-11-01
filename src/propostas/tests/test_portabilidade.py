import pytest

from propostas import selectors, services
from propostas.exceptions import TransicaoInvalida
from propostas.models import Proposta
from propostas.tests.factories import ModalidadeFactory, PropostaFactory, UsuarioFactory


@pytest.fixture
def usuario(db):
    return UsuarioFactory()


def _proposta(status, *, portabilidade):
    modalidade = ModalidadeFactory(envolve_portabilidade=portabilidade)
    return PropostaFactory(status=status, modalidade=modalidade)


def test_fluxo_completo_com_portabilidade(usuario):
    proposta = _proposta('enviada', portabilidade=True)

    for etapa in ['em_analise', 'aguardando_saldo', 'portabilidade_autorizada', 'aprovada']:
        services.avancar_proposta(usuario=usuario, proposta=proposta, status=etapa)

    proposta.refresh_from_db()
    assert proposta.status == Proposta.Status.APROVADA
    assert Proposta.Status.AGUARDANDO_SALDO.label == 'Aguardando saldo'
    assert Proposta.Status.PORTABILIDADE_AUTORIZADA.label == 'Portabilidade autorizada'


@pytest.mark.parametrize(
    ('inicial', 'alvo'),
    [
        ('em_analise', 'aprovada'),
        ('em_analise', 'portabilidade_autorizada'),
        ('enviada', 'aguardando_saldo'),
        ('aguardando_saldo', 'aprovada'),
        ('aguardando_saldo', 'em_analise'),
        ('portabilidade_autorizada', 'aguardando_saldo'),
        ('portabilidade_autorizada', 'em_analise'),
    ],
)
def test_transicoes_invalidas_com_portabilidade(usuario, inicial, alvo):
    proposta = _proposta(inicial, portabilidade=True)

    with pytest.raises(TransicaoInvalida):
        services.avancar_proposta(usuario=usuario, proposta=proposta, status=alvo)


@pytest.mark.parametrize('alvo', ['aguardando_saldo', 'portabilidade_autorizada'])
def test_sem_portabilidade_nao_marca_etapas_novas(usuario, alvo):
    proposta = _proposta('em_analise', portabilidade=False)

    with pytest.raises(TransicaoInvalida):
        services.avancar_proposta(usuario=usuario, proposta=proposta, status=alvo)


def test_sem_portabilidade_segue_fluxo_atual(usuario):
    proposta = _proposta('em_analise', portabilidade=False)

    services.avancar_proposta(usuario=usuario, proposta=proposta, status='aprovada')

    assert proposta.status == Proposta.Status.APROVADA


@pytest.mark.parametrize('inicial', ['aguardando_saldo', 'portabilidade_autorizada'])
def test_recusar_e_cancelar_das_etapas_novas(usuario, inicial):
    recusada = _proposta(inicial, portabilidade=True)
    cancelada = _proposta(inicial, portabilidade=True)

    services.recusar_proposta(usuario=usuario, proposta=recusada, motivo='Saldo negado')
    services.cancelar_proposta(usuario=usuario, proposta=cancelada, motivo='Desistiu')

    assert recusada.status == Proposta.Status.RECUSADA
    assert cancelada.status == Proposta.Status.CANCELADA


def test_historico_mostra_etapas_novas(usuario):
    proposta = _proposta('em_analise', portabilidade=True)
    services.avancar_proposta(usuario=usuario, proposta=proposta, status='aguardando_saldo')

    historico = selectors.historico_da_proposta(proposta=proposta)

    assert historico[0].get_status_display() == 'Aguardando saldo'
