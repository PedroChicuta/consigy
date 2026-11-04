import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from contratos.models import Contrato
from contratos.tests.factories import ContratoFactory


def _entrar(client, grupo):
    usuario = get_user_model().objects.create_user(username=grupo.lower(), password='x')
    usuario.groups.add(Group.objects.get(name=grupo))
    client.force_login(usuario)
    return usuario


@pytest.mark.django_db
def test_operador_acompanha_contrato_pela_lista_e_ficha(client):
    _entrar(client, 'Operador')
    contrato = ContratoFactory()

    client.post(reverse('contratos:avancar', args=[contrato.pk, 'averbado']))

    contrato.refresh_from_db()
    assert contrato.status == Contrato.Status.AVERBADO
    url = reverse('contratos:detalhe', args=[contrato.pk])
    filtrada = client.get(
        reverse('contratos:lista'), {'status': 'averbado'}, HTTP_HX_REQUEST='true'
    )
    assert url in filtrada.content.decode()
    outra = client.get(reverse('contratos:lista'), {'status': 'pago'})
    assert url not in outra.content.decode()
    ficha = client.get(url)
    assert 'Histórico de status' not in ficha.content.decode()

    client.post(reverse('contratos:cancelar', args=[contrato.pk]), {'motivo': 'Banco não pagou'})
    contrato.refresh_from_db()
    assert contrato.status == Contrato.Status.CANCELADO


@pytest.mark.django_db
def test_supervisor_audita_historico_avanca_etapas_e_cancela(client):
    _entrar(client, 'Supervisor')
    contrato = ContratoFactory()

    ficha = client.get(reverse('contratos:detalhe', args=[contrato.pk]))
    assert 'Histórico de status' in ficha.content.decode()

    client.post(reverse('contratos:avancar', args=[contrato.pk, 'averbado']))
    contrato.refresh_from_db()
    assert contrato.status == Contrato.Status.AVERBADO

    client.post(
        reverse('contratos:avancar', args=[contrato.pk, 'pago']),
        {'data_pagamento': '2026-10-15'},
    )
    contrato.refresh_from_db()
    assert contrato.status == Contrato.Status.PAGO

    client.post(reverse('contratos:avancar', args=[contrato.pk, 'quitado']))
    contrato.refresh_from_db()
    assert contrato.status == Contrato.Status.QUITADO

    outro = ContratoFactory()
    client.post(reverse('contratos:cancelar', args=[outro.pk]), {'motivo': 'Falha na averbação'})
    outro.refresh_from_db()
    assert outro.status == Contrato.Status.CANCELADO
