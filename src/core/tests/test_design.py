import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


@pytest.fixture
def client_logado(client, db):
    client.force_login(get_user_model().objects.create_user(username='maria', password='x'))
    return client


def test_design_responde_200_com_debug_para_autenticado(client_logado, settings):
    settings.DEBUG = True

    resposta = client_logado.get(reverse('design'))

    assert resposta.status_code == 200
    html = resposta.content.decode()
    assert 'id="botao-tema"' in html
    for texto in ('Aprovada', 'Formalizada', 'Recusada', 'Averbado', 'Pago'):
        assert texto in html
    for marca in ('<table', 'alert alert-', 'class="card"', 'pagination', 'form-control'):
        assert marca in html


def test_design_redireciona_anonimo_para_login(client, settings):
    settings.DEBUG = True

    resposta = client.get(reverse('design'))

    assert resposta.status_code == 302
    assert reverse('accounts:login') in resposta['Location']


def test_design_devolve_404_sem_debug(client_logado, settings):
    settings.DEBUG = False

    assert client_logado.get(reverse('design')).status_code == 404
