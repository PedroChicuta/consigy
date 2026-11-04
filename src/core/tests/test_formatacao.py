import datetime
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.template import Context, Template
from django.urls import reverse

from beneficios.tests.factories import BeneficioFactory, MargemFactory
from contratos.tests.factories import ContratoFactory
from core.formatacao import formatar_moeda, formatar_telefone
from propostas.models import Proposta
from propostas.tests.factories import PropostaFactory


@pytest.mark.parametrize(
    ('entrada', 'esperado'),
    [
        (Decimal('25000.00'), 'R$ 25.000,00'),
        (Decimal('25000'), 'R$ 25.000,00'),
        (Decimal('1234567.89'), 'R$ 1.234.567,89'),
        (Decimal('850.5'), 'R$ 850,50'),
        (Decimal('0'), 'R$ 0,00'),
        (Decimal('-1234.56'), '-R$ 1.234,56'),
        (25000, 'R$ 25.000,00'),
        ('9876.54', 'R$ 9.876,54'),
        (None, ''),
        ('', ''),
        ('invalido', 'invalido'),
    ],
)
def test_formatar_moeda_em_reais(entrada, esperado):
    assert formatar_moeda(entrada) == esperado


def test_filtro_moeda_disponivel_nos_templates():
    html = Template('{{ valor|moeda }}').render(Context({'valor': Decimal('25000.00')}))

    assert html == 'R$ 25.000,00'


@pytest.mark.parametrize(
    ('entrada', 'esperado'),
    [
        ('11988887777', '(11) 98888-7777'),
        ('1133334444', '(11) 3333-4444'),
        ('(11) 98888-7777', '(11) 98888-7777'),
        ('11 3333-4444', '(11) 3333-4444'),
        ('988887777', '988887777'),
        ('123', '123'),
        ('5511988887777', '5511988887777'),
        ('+55 3333-4444', '+55 3333-4444'),
        ('ramal 1234567890', 'ramal 1234567890'),
        (None, ''),
        ('', ''),
    ],
)
def test_formatar_telefone_no_padrao_brasileiro(entrada, esperado):
    assert formatar_telefone(entrada) == esperado


def test_filtro_telefone_disponivel_nos_templates():
    html = Template('{{ tel|telefone }}').render(Context({'tel': '11988887777'}))

    assert html == '(11) 98888-7777'


def test_moeda_formatada_em_beneficios_propostas_e_contratos(client, db):
    operador = get_user_model().objects.create_user(username='op_moeda', password='x')
    operador.groups.add(Group.objects.get(name='Operador'))
    client.force_login(operador)

    beneficio = BeneficioFactory()
    MargemFactory(
        beneficio=beneficio,
        valor=Decimal('1250.40'),
        data_consulta=datetime.date.today() - datetime.timedelta(days=5),
    )
    MargemFactory(
        beneficio=beneficio,
        valor=Decimal('2345.67'),
        data_consulta=datetime.date.today(),
    )
    html_beneficio = client.get(reverse('beneficios:detalhe', args=[beneficio.pk])).content.decode()
    assert 'R$ 2.345,67' in html_beneficio
    assert 'R$ 1.250,40' in html_beneficio

    proposta = PropostaFactory(
        beneficio=beneficio,
        status=Proposta.Status.FORMALIZADA,
        valor=Decimal('25000.00'),
        valor_liberado=Decimal('21500.50'),
        parcela=Decimal('1050.75'),
    )
    contrato = ContratoFactory(
        proposta=proposta,
        valor=Decimal('25000.00'),
        valor_liberado=Decimal('21500.50'),
        parcela=Decimal('1050.75'),
    )

    html_lista_propostas = client.get(reverse('propostas:lista')).content.decode()
    assert 'R$ 25.000,00' in html_lista_propostas
    assert 'R$ 21.500,50' in html_lista_propostas

    html_detalhe_proposta = client.get(
        reverse('propostas:detalhe', args=[proposta.pk])
    ).content.decode()
    assert 'R$ 25.000,00' in html_detalhe_proposta
    assert 'R$ 21.500,50' in html_detalhe_proposta
    assert 'R$ 1.050,75' in html_detalhe_proposta
    assert 'Valor: R$ 25.000,00' in html_detalhe_proposta
    assert 'Parcela: R$ 1.050,75' in html_detalhe_proposta

    html_lista_contratos = client.get(reverse('contratos:lista')).content.decode()
    assert 'R$ 25.000,00' in html_lista_contratos
    assert 'R$ 21.500,50' in html_lista_contratos
    assert 'R$ 1.050,75' in html_lista_contratos

    html_detalhe_contrato = client.get(
        reverse('contratos:detalhe', args=[contrato.pk])
    ).content.decode()
    assert 'R$ 25.000,00' in html_detalhe_contrato
    assert 'R$ 21.500,50' in html_detalhe_contrato
    assert 'R$ 1.050,75' in html_detalhe_contrato
