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


def test_saudacao_usa_nome_completo(client, db):
    user = get_user_model().objects.create_user(
        username='maria', password='x', first_name='Maria', last_name='Silva'
    )
    client.force_login(user)

    html = client.get(reverse('inicio:index')).content.decode()

    assert 'Olá, Maria Silva!' in html
    assert 'Atualizar saudação' not in html


def test_saudacao_cai_para_username_sem_nome(client_logado):
    html = client_logado.get(reverse('inicio:index')).content.decode()

    assert 'Olá, maria!' in html
