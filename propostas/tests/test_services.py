import datetime
from decimal import Decimal

import pytest

from bancos.tests.factories import BancoFactory
from beneficios.tests.factories import BeneficioFactory, MargemFactory
from propostas import services
from propostas.exceptions import (
    BancoInativo,
    BeneficioInativo,
    BeneficioSemMargem,
    CondicoesInvalidas,
    MargemAntigaSemConfirmacao,
    ParcelaAcimaDaMargem,
    PropostaNaoDigitada,
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


def _proposta_com_margem(*, parcela='250.00', margem='350.00', dias=0):
    proposta = PropostaFactory(parcela=Decimal(parcela))
    MargemFactory(
        beneficio=proposta.beneficio,
        valor=Decimal(margem),
        data_consulta=datetime.date.today() - datetime.timedelta(days=dias),
    )
    return proposta


def test_envia_proposta_digitada(usuario):
    proposta = _proposta_com_margem()

    services.enviar_proposta(usuario=usuario, proposta=proposta)

    proposta.refresh_from_db()
    assert proposta.status == Proposta.Status.ENVIADA
    assert proposta.history.first().history_user == usuario


def test_parcela_igual_a_margem_pode_ser_enviada(usuario):
    proposta = _proposta_com_margem(parcela='350.00', margem='350.00')

    services.enviar_proposta(usuario=usuario, proposta=proposta)

    assert proposta.status == Proposta.Status.ENVIADA


def test_bloqueia_parcela_acima_da_margem_com_valores_na_mensagem(usuario):
    proposta = _proposta_com_margem(parcela='400.00', margem='350.00')

    with pytest.raises(ParcelaAcimaDaMargem) as erro:
        services.enviar_proposta(usuario=usuario, proposta=proposta)

    assert '400.00' in str(erro.value)
    assert '350.00' in str(erro.value)
    proposta.refresh_from_db()
    assert proposta.status == Proposta.Status.DIGITADA


def test_parcela_acima_da_margem_nao_passa_nem_com_confirmacao(usuario):
    proposta = _proposta_com_margem(parcela='400.00', margem='350.00', dias=60)

    with pytest.raises(ParcelaAcimaDaMargem):
        services.enviar_proposta(usuario=usuario, proposta=proposta, confirmar_margem_antiga=True)


def test_margem_antiga_exige_confirmacao(usuario):
    proposta = _proposta_com_margem(dias=31)

    with pytest.raises(MargemAntigaSemConfirmacao):
        services.enviar_proposta(usuario=usuario, proposta=proposta)

    proposta.refresh_from_db()
    assert proposta.status == Proposta.Status.DIGITADA


def test_margem_antiga_envia_com_confirmacao(usuario):
    proposta = _proposta_com_margem(dias=31)

    services.enviar_proposta(usuario=usuario, proposta=proposta, confirmar_margem_antiga=True)

    assert proposta.status == Proposta.Status.ENVIADA


def test_margem_de_30_dias_nao_e_antiga(usuario):
    proposta = _proposta_com_margem(dias=30)

    services.enviar_proposta(usuario=usuario, proposta=proposta)

    assert proposta.status == Proposta.Status.ENVIADA


def test_nao_envia_sem_margem(usuario):
    proposta = PropostaFactory()

    with pytest.raises(BeneficioSemMargem):
        services.enviar_proposta(usuario=usuario, proposta=proposta)


def test_so_envia_proposta_digitada(usuario):
    proposta = _proposta_com_margem()
    services.enviar_proposta(usuario=usuario, proposta=proposta)

    with pytest.raises(PropostaNaoDigitada):
        services.enviar_proposta(usuario=usuario, proposta=proposta)


def test_enviada_trava_condicoes_mas_aceita_observacoes(usuario):
    proposta = _proposta_com_margem()
    services.enviar_proposta(usuario=usuario, proposta=proposta)

    with pytest.raises(PropostaTravada):
        services.editar_proposta(
            usuario=usuario,
            proposta=proposta,
            beneficio=proposta.beneficio,
            banco=proposta.banco,
            **{**CONDICOES, 'valor': Decimal('1.00')},
        )
    services.editar_observacoes(usuario=usuario, proposta=proposta, observacoes='ok')
    proposta.refresh_from_db()
    assert proposta.observacoes == 'ok'
