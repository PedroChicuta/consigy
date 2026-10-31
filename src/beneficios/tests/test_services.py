import datetime
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from beneficios import selectors, services
from beneficios.exceptions import (
    BeneficioJaInativo,
    ClienteInativo,
    MargemInvalida,
    NumeroDuplicado,
)
from beneficios.models import Beneficio
from beneficios.tests.factories import BeneficioFactory, MargemFactory
from clientes.tests.factories import ClienteFactory


@pytest.fixture
def usuario(db):
    return get_user_model().objects.create_user(username='op', password='x')


def test_cria_beneficio_ativo_com_historico(usuario):
    cliente = ClienteFactory()

    beneficio = services.criar_beneficio(
        usuario=usuario, cliente=cliente, numero='1234567890', especie=Beneficio.Especie.PENSAO
    )

    assert beneficio.ativo
    assert beneficio.especie == 'pensao'
    assert beneficio.history.first().history_user == usuario


def test_cliente_pode_ter_varios_beneficios(usuario):
    cliente = ClienteFactory()
    services.criar_beneficio(usuario=usuario, cliente=cliente, numero='1', especie='pensao')
    services.criar_beneficio(usuario=usuario, cliente=cliente, numero='2', especie='aposentadoria')

    assert cliente.beneficios.count() == 2


def test_numero_duplicado_e_recusado(usuario):
    BeneficioFactory(numero='999')

    with pytest.raises(NumeroDuplicado):
        services.criar_beneficio(
            usuario=usuario, cliente=ClienteFactory(), numero='999', especie='pensao'
        )


def test_numero_e_normalizado(usuario):
    BeneficioFactory(numero='1234567890')

    with pytest.raises(NumeroDuplicado):
        services.criar_beneficio(
            usuario=usuario, cliente=ClienteFactory(), numero=' 123.456.789-0 ', especie='pensao'
        )


def test_cliente_inativo_nao_recebe_beneficio(usuario):
    cliente = ClienteFactory(ativo=False)

    with pytest.raises(ClienteInativo):
        services.criar_beneficio(usuario=usuario, cliente=cliente, numero='5', especie='pensao')


def test_inativar_beneficio_nunca_exclui(usuario):
    beneficio = BeneficioFactory()

    services.inativar_beneficio(usuario=usuario, beneficio=beneficio)

    beneficio.refresh_from_db()
    assert not beneficio.ativo
    with pytest.raises(BeneficioJaInativo):
        services.inativar_beneficio(usuario=usuario, beneficio=beneficio)


def test_margem_vigente_e_a_de_consulta_mais_recente(usuario):
    beneficio = BeneficioFactory()
    hoje = datetime.date.today()
    services.registrar_margem(
        usuario=usuario,
        beneficio=beneficio,
        valor=Decimal('100.00'),
        data_consulta=hoje - datetime.timedelta(days=10),
    )
    services.registrar_margem(
        usuario=usuario, beneficio=beneficio, valor=Decimal('200.50'), data_consulta=hoje
    )
    # Registrada depois, mas com consulta mais antiga: não é a vigente.
    services.registrar_margem(
        usuario=usuario,
        beneficio=beneficio,
        valor=Decimal('50.00'),
        data_consulta=hoje - datetime.timedelta(days=20),
    )

    assert selectors.margem_vigente(beneficio=beneficio).valor == Decimal('200.50')
    assert [m.valor for m in selectors.historico_de_margens(beneficio=beneficio)] == [
        Decimal('200.50'),
        Decimal('100.00'),
        Decimal('50.00'),
    ]


@pytest.mark.parametrize('valor', [Decimal('-1'), Decimal('0')])
def test_margem_nao_positiva_e_recusada(usuario, valor):
    with pytest.raises(MargemInvalida):
        services.registrar_margem(
            usuario=usuario,
            beneficio=BeneficioFactory(),
            valor=valor,
            data_consulta=datetime.date.today(),
        )


def test_margem_com_data_futura_e_recusada(usuario):
    with pytest.raises(MargemInvalida):
        services.registrar_margem(
            usuario=usuario,
            beneficio=BeneficioFactory(),
            valor=Decimal('10'),
            data_consulta=datetime.date.today() + datetime.timedelta(days=1),
        )


@pytest.mark.parametrize(('dias', 'antiga'), [(0, False), (30, False), (31, True), (90, True)])
def test_margem_com_mais_de_30_dias_e_antiga(db, dias, antiga):
    margem = MargemFactory(data_consulta=datetime.date.today() - datetime.timedelta(days=dias))

    assert margem.antiga is antiga


def test_beneficio_sem_margem_nao_tem_vigente(db):
    assert selectors.margem_vigente(beneficio=BeneficioFactory()) is None
