import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

SENHA = 'senha-forte-123'


@pytest.fixture
def operador(db):
    return get_user_model().objects.create_user(username='maria', password=SENHA)


def test_usuario_customizado_em_accounts():
    assert settings.AUTH_USER_MODEL == 'accounts.User'


@pytest.mark.parametrize('url', ['/', '/qualquer/coisa/', '/admin/'])
def test_anonimo_e_redirecionado_ao_login(client, url):
    resposta = client.get(url)

    assert resposta.status_code == 302
    assert resposta.url.startswith(reverse('accounts:login'))


def test_tela_de_login_e_publica_e_em_portugues(client):
    resposta = client.get(reverse('accounts:login'))

    assert resposta.status_code == 200
    assert 'Entrar' in resposta.content.decode()


def test_autenticado_em_entrar_e_redirecionado(client, operador):
    client.force_login(operador)

    resposta = client.get(reverse('accounts:login'))

    assert resposta.status_code == 302
    assert resposta.url == reverse('inicio:index')


def test_login_valido_entra(client, operador):
    resposta = client.post(reverse('accounts:login'), {'username': 'maria', 'password': SENHA})

    assert resposta.status_code == 302
    assert client.get('/').status_code == 200


def test_senha_errada_mostra_erro(client, operador):
    resposta = client.post(reverse('accounts:login'), {'username': 'maria', 'password': 'errada'})

    assert resposta.status_code == 200
    assert 'incorretos' in resposta.content.decode()
    assert client.get('/').status_code == 302


def test_sair_encerra_a_sessao(client, operador):
    client.force_login(operador)

    resposta = client.post(reverse('accounts:logout'))

    assert resposta.status_code == 302
    assert client.get('/').status_code == 302
