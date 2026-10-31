import datetime

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from beneficios.models import Beneficio, Margem
from beneficios.tests.factories import BeneficioFactory, MargemFactory
from clientes.tests.factories import ClienteFactory


@pytest.fixture
def operador(client, db):
    usuario = get_user_model().objects.create_user(username='operador', password='x')
    usuario.groups.add(Group.objects.get(name='Operador'))
    client.force_login(usuario)
    return usuario


def test_sem_permissao_e_barrado(client, db):
    client.force_login(get_user_model().objects.create_user(username='sem', password='x'))
    beneficio = BeneficioFactory()

    assert client.get(reverse('beneficios:detalhe', args=[beneficio.pk])).status_code == 403
    resposta = client.post(
        reverse('beneficios:criar', args=[beneficio.cliente.pk]),
        {'numero': '1', 'especie': 'pensao'},
    )
    assert resposta.status_code == 403
    assert Beneficio.objects.count() == 1


def test_operador_cadastra_beneficio_e_ve_na_ficha(client, operador):
    cliente = ClienteFactory()

    resposta = client.post(
        reverse('beneficios:criar', args=[cliente.pk]),
        {'numero': '1234567890', 'especie': 'pensao'},
        follow=True,
    )

    assert '1234567890' in resposta.content.decode()


def test_numero_duplicado_mostra_erro(client, operador):
    BeneficioFactory(numero='777')

    resposta = client.post(
        reverse('beneficios:criar', args=[ClienteFactory(cpf='11144477735').pk]),
        {'numero': '777', 'especie': 'pensao'},
    )

    assert 'Já existe um Benefício' in resposta.content.decode()


def test_operador_registra_margem_e_ve_aviso_de_margem_antiga(client, operador):
    beneficio = BeneficioFactory()
    antiga = datetime.date.today() - datetime.timedelta(days=45)

    resposta = client.post(
        reverse('beneficios:registrar_margem', args=[beneficio.pk]),
        {'valor': '321.50', 'data_consulta': antiga.isoformat()},
        follow=True,
    )

    corpo = resposta.content.decode()
    assert Margem.objects.count() == 1
    assert '321.50' in corpo or '321,50' in corpo
    assert 'nova consulta' in corpo


def test_margem_recente_nao_mostra_aviso(client, operador):
    beneficio = BeneficioFactory()
    MargemFactory(beneficio=beneficio)

    resposta = client.get(reverse('beneficios:detalhe', args=[beneficio.pk]))

    assert 'nova consulta' not in resposta.content.decode()


def test_operador_inativa_beneficio(client, operador):
    beneficio = BeneficioFactory()

    client.post(reverse('beneficios:inativar', args=[beneficio.pk]))

    beneficio.refresh_from_db()
    assert not beneficio.ativo
