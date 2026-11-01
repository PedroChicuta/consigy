import datetime
from decimal import Decimal

import pytest
from django.contrib.auth.models import Group

from bancos.tests.factories import BancoFactory
from beneficios.tests.factories import BeneficioFactory, MargemFactory
from propostas import selectors, services
from propostas.exceptions import (
    BancoInativo,
    BeneficioInativo,
    BeneficioSemMargem,
    CancelamentoSemPermissao,
    CondicoesInvalidas,
    MargemAntigaSemConfirmacao,
    MotivoObrigatorio,
    ParcelaAcimaDaMargem,
    PropostaNaoDigitada,
    PropostaTravada,
    TransicaoInvalida,
)
from propostas.models import Proposta
from propostas.tests.factories import ModalidadeFactory, PropostaFactory, UsuarioFactory

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
        modalidade=ModalidadeFactory(),
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
            modalidade=ModalidadeFactory(),
            **CONDICOES,
        )
    assert not Proposta.objects.exists()


def test_nao_cria_com_beneficio_inativo(usuario):
    with pytest.raises(BeneficioInativo):
        services.criar_proposta(
            usuario=usuario,
            beneficio=BeneficioFactory(ativo=False),
            banco=BancoFactory(),
            modalidade=ModalidadeFactory(),
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
            **{**CONDICOES, 'modalidade': ModalidadeFactory(), campo: valor},
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
        modalidade=ModalidadeFactory(),
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
            modalidade=ModalidadeFactory(),
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
        modalidade=ModalidadeFactory(),
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
            modalidade=ModalidadeFactory(),
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
            **{**CONDICOES, 'modalidade': ModalidadeFactory(), 'valor': Decimal('1.00')},
        )
    services.editar_observacoes(usuario=usuario, proposta=proposta, observacoes='ok')
    proposta.refresh_from_db()
    assert proposta.observacoes == 'ok'


# --- Acompanhamento e encerramento ---


def _com_status(status):
    return PropostaFactory(status=status)


def test_avanca_na_ordem(usuario):
    proposta = _com_status(Proposta.Status.ENVIADA)

    services.avancar_proposta(usuario=usuario, proposta=proposta, status='em_analise')
    services.avancar_proposta(usuario=usuario, proposta=proposta, status='aprovada')

    proposta.refresh_from_db()
    assert proposta.status == Proposta.Status.APROVADA


@pytest.mark.parametrize(
    ('inicial', 'alvo'),
    [
        ('enviada', 'aprovada'),
        ('digitada', 'em_analise'),
        ('aprovada', 'em_analise'),
        ('enviada', 'formalizada'),
    ],
)
def test_nao_pula_nem_volta_etapa(usuario, inicial, alvo):
    proposta = _com_status(inicial)

    with pytest.raises(TransicaoInvalida):
        services.avancar_proposta(usuario=usuario, proposta=proposta, status=alvo)


@pytest.mark.parametrize('inicial', ['digitada', 'enviada', 'em_analise', 'aprovada'])
def test_recusa_de_qualquer_etapa_antes_de_formalizada(usuario, inicial):
    proposta = _com_status(inicial)

    services.recusar_proposta(usuario=usuario, proposta=proposta, motivo='Idade acima do limite')

    proposta.refresh_from_db()
    assert proposta.status == Proposta.Status.RECUSADA
    assert proposta.motivo == 'Idade acima do limite'


@pytest.mark.parametrize('inicial', ['digitada', 'enviada', 'em_analise'])
def test_operador_cancela_ate_em_analise(usuario, inicial):
    proposta = _com_status(inicial)

    services.cancelar_proposta(usuario=usuario, proposta=proposta, motivo='Cliente desistiu')

    proposta.refresh_from_db()
    assert proposta.status == Proposta.Status.CANCELADA
    assert proposta.motivo == 'Cliente desistiu'


@pytest.mark.parametrize('funcao', ['cancelar_proposta', 'recusar_proposta'])
@pytest.mark.parametrize('motivo', ['', '   '])
def test_motivo_e_obrigatorio(usuario, funcao, motivo):
    proposta = _com_status('enviada')

    with pytest.raises(MotivoObrigatorio):
        getattr(services, funcao)(usuario=usuario, proposta=proposta, motivo=motivo)

    proposta.refresh_from_db()
    assert proposta.status == Proposta.Status.ENVIADA


def test_operador_nao_cancela_aprovada(usuario):
    proposta = _com_status('aprovada')

    with pytest.raises(CancelamentoSemPermissao):
        services.cancelar_proposta(usuario=usuario, proposta=proposta, motivo='Desistência')


def test_supervisor_cancela_aprovada(usuario):
    usuario.groups.add(Group.objects.get(name='Supervisor'))
    proposta = _com_status('aprovada')

    services.cancelar_proposta(usuario=usuario, proposta=proposta, motivo='Desistência')

    proposta.refresh_from_db()
    assert proposta.status == Proposta.Status.CANCELADA


@pytest.mark.parametrize('final', ['formalizada', 'recusada', 'cancelada'])
def test_finais_nao_reabrem_nem_encerram_de_novo(usuario, final):
    proposta = _com_status(final)

    with pytest.raises(TransicaoInvalida):
        services.cancelar_proposta(usuario=usuario, proposta=proposta, motivo='x')
    with pytest.raises(TransicaoInvalida):
        services.recusar_proposta(usuario=usuario, proposta=proposta, motivo='x')
    with pytest.raises(TransicaoInvalida):
        services.avancar_proposta(usuario=usuario, proposta=proposta, status='em_analise')


def test_historico_registra_autor_e_status(usuario):
    proposta = _com_status('enviada')
    services.avancar_proposta(usuario=usuario, proposta=proposta, status='em_analise')

    historico = selectors.historico_da_proposta(proposta=proposta)

    assert historico[0].status == 'em_analise'
    assert historico[0].history_user == usuario
