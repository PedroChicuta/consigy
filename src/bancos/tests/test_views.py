import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from bancos.models import Banco
from bancos.tests.factories import BancoFactory


def _logar(client, grupo):
    usuario = get_user_model().objects.create_user(username=grupo.lower(), password='x')
    usuario.groups.add(Group.objects.get(name=grupo))
    client.force_login(usuario)
    return usuario


@pytest.fixture
def operador(client, db):
    return _logar(client, 'Operador')


@pytest.fixture
def supervisor(client, db):
    return _logar(client, 'Supervisor')


def test_sem_permissao_e_barrado(client, db):
    client.force_login(get_user_model().objects.create_user(username='sem', password='x'))

    assert client.get(reverse('bancos:lista')).status_code == 403


def test_operador_ve_lista_sem_acoes_de_alteracao(client, operador):
    banco = BancoFactory(nome='Banco Alfa')

    resposta = client.get(reverse('bancos:lista'))

    conteudo = resposta.content.decode()
    assert 'Banco Alfa' in conteudo
    assert 'Novo Banco' not in conteudo
    assert reverse('bancos:editar', args=[banco.pk]) not in conteudo


def test_operador_nao_cria_edita_nem_inativa(client, operador):
    banco = BancoFactory()

    assert client.get(reverse('bancos:criar')).status_code == 403
    assert client.post(reverse('bancos:criar'), {'nome': 'X', 'codigo': '1'}).status_code == 403
    assert client.post(reverse('bancos:editar', args=[banco.pk]), {}).status_code == 403
    assert client.post(reverse('bancos:inativar', args=[banco.pk])).status_code == 403
    banco.refresh_from_db()
    assert banco.ativo
    assert Banco.objects.count() == 1


def test_supervisor_cria_edita_inativa_e_reativa(client, supervisor):
    client.post(reverse('bancos:criar'), {'nome': 'Banco Alfa', 'codigo': '001'})
    banco = Banco.objects.get()

    client.post(reverse('bancos:editar', args=[banco.pk]), {'nome': 'Alfa SA', 'codigo': '001'})
    client.post(reverse('bancos:inativar', args=[banco.pk]))
    banco.refresh_from_db()
    assert banco.nome == 'Alfa SA'
    assert not banco.ativo

    client.post(reverse('bancos:reativar', args=[banco.pk]))
    banco.refresh_from_db()
    assert banco.ativo


def test_codigo_duplicado_mostra_erro_no_formulario(client, supervisor):
    BancoFactory(codigo='001')

    resposta = client.post(reverse('bancos:criar'), {'nome': 'Outro', 'codigo': '001'})

    assert resposta.status_code == 200
    assert 'Já existe um Banco com este código' in resposta.content.decode()
