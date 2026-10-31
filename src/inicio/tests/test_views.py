import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


@pytest.fixture
def client_logado(client, db):
    client.force_login(get_user_model().objects.create_user(username='maria', password='x'))
    return client


def test_pagina_inicial_usa_layout_base(client_logado):
    resposta = client_logado.get(reverse('inicio:index'))

    assert resposta.status_code == 200
    html = resposta.content.decode()
    assert '<html lang="pt-br">' in html
    assert 'bootstrap' in html
    assert 'htmx' in html
    assert 'Início' in html


def test_requisicao_htmx_devolve_so_o_fragmento(client_logado):
    resposta = client_logado.get(reverse('inicio:index'), headers={'HX-Request': 'true'})

    assert resposta.status_code == 200
    html = resposta.content.decode()
    assert '<html' not in html
    assert 'id="saudacao"' in html
