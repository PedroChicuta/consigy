import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


@pytest.fixture
def usuario(db):
    return get_user_model().objects.create_user(username='maria', password='x')


def test_botao_de_tema_aparece_para_usuario_autenticado(client, usuario):
    client.force_login(usuario)

    html = client.get(reverse('inicio:index')).content.decode()

    assert 'id="botao-tema"' in html
    assert 'aria-label="Mudar para tema escuro"' in html


def test_botao_de_tema_nao_aparece_para_anonimo(client, db):
    html = client.get(reverse('accounts:login')).content.decode()

    assert 'id="botao-tema"' not in html


def test_script_de_tema_fica_no_head_das_paginas_autenticadas(client, usuario):
    client.force_login(usuario)

    html = client.get(reverse('inicio:index')).content.decode()

    assert 'tema.js' in html.split('</head>')[0]


def test_script_de_tema_fica_no_head_do_login(client, db):
    html = client.get(reverse('accounts:login')).content.decode()

    assert 'tema.js' in html.split('</head>')[0]
