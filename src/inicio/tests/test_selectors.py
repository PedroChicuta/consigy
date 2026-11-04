import datetime
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from bancos.models import Banco
from beneficios.models import Beneficio
from clientes.models import Cliente
from contratos.models import Contrato
from inicio import selectors
from propostas.models import Modalidade, Proposta

User = get_user_model()


@pytest.fixture
def operador(db):
    user = User.objects.create_user(username='operador1', password='x')
    grupo, _ = Group.objects.get_or_create(name='Operador')
    user.groups.add(grupo)
    return user


@pytest.fixture
def supervisor(db):
    user = User.objects.create_user(username='supervisor1', password='x')
    grupo, _ = Group.objects.get_or_create(name='Supervisor')
    user.groups.add(grupo)
    return user


@pytest.fixture
def cliente(db):
    return Cliente.objects.create(
        nome='Maria Santos',
        cpf='52998224725',
        data_nascimento='1960-01-01',
        telefone='11988887777',
    )


@pytest.fixture
def banco(db):
    return Banco.objects.create(nome='Banco Alfa', codigo='001')


@pytest.fixture
def modalidade(db):
    return Modalidade.objects.create(nome='Novo')


def test_buscar_clientes_atendimento_vazio_retorna_vazio(cliente):
    assert selectors.buscar_clientes_atendimento(busca='').count() == 0
    assert selectors.buscar_clientes_atendimento(busca='   ').count() == 0


def test_buscar_clientes_atendimento_por_nome_e_beneficios_ativos(cliente):
    Beneficio.objects.create(
        cliente=cliente, numero='1111111111', especie=Beneficio.Especie.APOSENTADORIA, ativo=True
    )
    Beneficio.objects.create(
        cliente=cliente, numero='2222222222', especie=Beneficio.Especie.PENSAO, ativo=False
    )
    outro = Cliente.objects.create(
        nome='João Silva',
        cpf='15350946056',
        data_nascimento='1970-01-01',
        telefone='11977776666',
    )

    resultado = selectors.buscar_clientes_atendimento(busca='Maria')

    assert list(resultado) == [cliente]
    assert resultado[0].total_beneficios_ativos == 1

    resultado_outro = selectors.buscar_clientes_atendimento(busca='João')
    assert list(resultado_outro) == [outro]
    assert resultado_outro[0].total_beneficios_ativos == 0


def test_buscar_clientes_atendimento_por_cpf_com_e_sem_mascara(cliente):
    assert list(selectors.buscar_clientes_atendimento(busca='52998224725')) == [cliente]
    assert list(selectors.buscar_clientes_atendimento(busca='529.982.247-25')) == [cliente]
    assert list(selectors.buscar_clientes_atendimento(busca='982247')) == [cliente]


def test_verificar_cpf_inedito_com_cpf_valido_sem_cadastro(db):
    cpf_valido_inedito = '15350946056'
    assert selectors.verificar_cpf_inedito(busca=cpf_valido_inedito) == cpf_valido_inedito
    assert selectors.verificar_cpf_inedito(busca='153.509.460-56') == cpf_valido_inedito


def test_verificar_cpf_inedito_com_cpf_existente(cliente):
    assert selectors.verificar_cpf_inedito(busca=cliente.cpf) is None
    assert selectors.verificar_cpf_inedito(busca=cliente.cpf_formatado) is None


def test_verificar_cpf_inedito_com_cpf_invalido(db):
    assert selectors.verificar_cpf_inedito(busca='11111111111') is None
    assert selectors.verificar_cpf_inedito(busca='12345678900') is None
    assert selectors.verificar_cpf_inedito(busca='123') is None


def test_verificar_cpf_inedito_com_busca_por_nome(db):
    assert selectors.verificar_cpf_inedito(busca='Maria Santos') is None


def test_listar_propostas_em_andamento_filtra_status(operador, cliente, banco, modalidade):
    beneficio = Beneficio.objects.create(
        cliente=cliente, numero='3333333333', especie=Beneficio.Especie.APOSENTADORIA
    )
    p_digitada = Proposta.objects.create(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=operador,
        status=Proposta.Status.DIGITADA,
        valor=Decimal('5000'),
        valor_liberado=Decimal('5000'),
        prazo=48,
        parcela=Decimal('150'),
        taxa=Decimal('1.8'),
    )
    p_enviada = Proposta.objects.create(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=operador,
        status=Proposta.Status.ENVIADA,
        valor=Decimal('5000'),
        valor_liberado=Decimal('5000'),
        prazo=48,
        parcela=Decimal('150'),
        taxa=Decimal('1.8'),
    )
    p_aprovada = Proposta.objects.create(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=operador,
        status=Proposta.Status.APROVADA,
        valor=Decimal('5000'),
        valor_liberado=Decimal('5000'),
        prazo=48,
        parcela=Decimal('150'),
        taxa=Decimal('1.8'),
    )
    # Status encerrados não devem aparecer
    Proposta.objects.create(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=operador,
        status=Proposta.Status.FORMALIZADA,
        valor=Decimal('5000'),
        valor_liberado=Decimal('5000'),
        prazo=48,
        parcela=Decimal('150'),
        taxa=Decimal('1.8'),
    )
    Proposta.objects.create(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=operador,
        status=Proposta.Status.RECUSADA,
        valor=Decimal('5000'),
        valor_liberado=Decimal('5000'),
        prazo=48,
        parcela=Decimal('150'),
        taxa=Decimal('1.8'),
    )
    Proposta.objects.create(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=operador,
        status=Proposta.Status.CANCELADA,
        valor=Decimal('5000'),
        valor_liberado=Decimal('5000'),
        prazo=48,
        parcela=Decimal('150'),
        taxa=Decimal('1.8'),
    )

    resultado = list(selectors.listar_propostas_em_andamento())
    assert set(resultado) == {p_digitada, p_enviada, p_aprovada}


def test_listar_propostas_em_andamento_filtro_minhas(
    operador, supervisor, cliente, banco, modalidade
):
    beneficio = Beneficio.objects.create(
        cliente=cliente, numero='4444444444', especie=Beneficio.Especie.APOSENTADORIA
    )
    p_minha = Proposta.objects.create(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=operador,
        status=Proposta.Status.DIGITADA,
        valor=Decimal('5000'),
        valor_liberado=Decimal('5000'),
        prazo=48,
        parcela=Decimal('150'),
        taxa=Decimal('1.8'),
    )
    p_outra = Proposta.objects.create(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=supervisor,
        status=Proposta.Status.DIGITADA,
        valor=Decimal('5000'),
        valor_liberado=Decimal('5000'),
        prazo=48,
        parcela=Decimal('150'),
        taxa=Decimal('1.8'),
    )

    minhas = selectors.listar_propostas_em_andamento(usuario=operador, apenas_minhas=True)
    assert list(minhas) == [p_minha]
    todas = selectors.listar_propostas_em_andamento(usuario=operador, apenas_minhas=False)
    assert set(todas) == {p_minha, p_outra}


def test_listar_contratos_pendentes_filtra_status(operador, cliente, banco, modalidade):
    beneficio = Beneficio.objects.create(
        cliente=cliente, numero='5555555555', especie=Beneficio.Especie.APOSENTADORIA
    )
    p1 = Proposta.objects.create(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=operador,
        status=Proposta.Status.FORMALIZADA,
        valor=Decimal('5000'),
        valor_liberado=Decimal('5000'),
        prazo=48,
        parcela=Decimal('150'),
        taxa=Decimal('1.8'),
    )
    p2 = Proposta.objects.create(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=operador,
        status=Proposta.Status.FORMALIZADA,
        valor=Decimal('6000'),
        valor_liberado=Decimal('6000'),
        prazo=48,
        parcela=Decimal('180'),
        taxa=Decimal('1.8'),
    )
    p3 = Proposta.objects.create(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=operador,
        status=Proposta.Status.FORMALIZADA,
        valor=Decimal('7000'),
        valor_liberado=Decimal('7000'),
        prazo=48,
        parcela=Decimal('200'),
        taxa=Decimal('1.8'),
    )

    c_formalizado = Contrato.objects.create(
        proposta=p1,
        modalidade=modalidade,
        status=Contrato.Status.FORMALIZADO,
        valor=p1.valor,
        valor_liberado=p1.valor_liberado,
        prazo=p1.prazo,
        parcela=p1.parcela,
        taxa=p1.taxa,
    )
    c_averbado = Contrato.objects.create(
        proposta=p2,
        modalidade=modalidade,
        status=Contrato.Status.AVERBADO,
        valor=p2.valor,
        valor_liberado=p2.valor_liberado,
        prazo=p2.prazo,
        parcela=p2.parcela,
        taxa=p2.taxa,
    )
    # Contrato pago não deve aparecer em pendentes
    Contrato.objects.create(
        proposta=p3,
        modalidade=modalidade,
        status=Contrato.Status.PAGO,
        valor=p3.valor,
        valor_liberado=p3.valor_liberado,
        prazo=p3.prazo,
        parcela=p3.parcela,
        taxa=p3.taxa,
        data_pagamento=datetime.date.today(),
    )

    resultado = list(selectors.listar_contratos_pendentes())
    assert set(resultado) == {c_formalizado, c_averbado}


def test_definir_escopo_padrao_supervisor_vs_operador(operador, supervisor):
    assert selectors.definir_escopo_padrao_propostas(usuario=operador) == 'minhas'
    assert selectors.definir_escopo_padrao_propostas(usuario=supervisor) == 'todas'
