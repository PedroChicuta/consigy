import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_pagina_inicial_usa_layout_base(client):
    resposta = client.get(reverse('inicio:index'))

    assert resposta.status_code == 200
    html = resposta.content.decode()
    assert '<html lang="pt-br">' in html
    assert 'bootstrap' in html
    assert 'htmx' in html
    assert 'Início' in html


def test_requisicao_htmx_devolve_so_o_fragmento(client):
    resposta = client.get(reverse('inicio:index'), headers={'HX-Request': 'true'})

    assert resposta.status_code == 200
    html = resposta.content.decode()
    assert '<html' not in html
    assert 'id="saudacao"' in html
