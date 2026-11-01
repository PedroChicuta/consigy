from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

import core

CSS_BOOTSTRAP = 'bootstrap@5.3.3/dist/css/bootstrap.min.css'
CSS_TEMA = 'tema.css'


def _tema_vem_depois_do_bootstrap(html):
    assert CSS_BOOTSTRAP in html
    assert CSS_TEMA in html
    assert html.index(CSS_TEMA) > html.index(CSS_BOOTSTRAP)


@pytest.mark.django_db
def test_pagina_autenticada_referencia_tema_depois_do_bootstrap(client):
    client.force_login(get_user_model().objects.create_user(username='maria', password='x'))

    resposta = client.get(reverse('inicio:index'))

    _tema_vem_depois_do_bootstrap(resposta.content.decode())


@pytest.mark.django_db
def test_login_referencia_tema_depois_do_bootstrap(client):
    resposta = client.get(reverse('accounts:login'))

    assert resposta.status_code == 200
    _tema_vem_depois_do_bootstrap(resposta.content.decode())


def test_arquivo_de_tema_usa_verde_escuro_e_nao_altera_sucesso():
    css = (Path(core.__file__).parent / 'static' / 'tema.css').read_text()

    assert '#14532d' in css
    assert '--bs-success' not in css
