import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from clientes.models import Cliente
from clientes.tests.factories import ClienteFactory

DADOS = {
    'nome': 'José da Silva',
    'cpf': '529.982.247-25',
    'data_nascimento': '1948-03-02',
    'telefone': '(11) 98888-7777',
    'email': '',
}


def _usuario(grupo):
    usuario = get_user_model().objects.create_user(username=grupo.lower(), password='x')
    usuario.groups.add(Group.objects.get(name=grupo))
    return usuario


@pytest.fixture
def operador(client, db):
    usuario = _usuario('Operador')
    client.force_login(usuario)
    return usuario


@pytest.fixture
def supervisor(client, db):
    usuario = _usuario('Supervisor')
    client.force_login(usuario)
    return usuario


def test_sem_permissao_e_barrado(client, db):
    client.force_login(get_user_model().objects.create_user(username='sem', password='x'))

    assert client.get(reverse('clientes:lista')).status_code == 403
    assert client.post(reverse('clientes:criar'), DADOS).status_code == 403
    assert not Cliente.objects.exists()


def test_operador_cadastra_cliente_e_ve_ficha_com_cpf_completo(client, operador):
    resposta = client.post(reverse('clientes:criar'), DADOS, follow=True)

    assert resposta.status_code == 200
    assert '529.982.247-25' in resposta.content.decode()


def test_cpf_invalido_mostra_erro_no_formulario(client, operador):
    resposta = client.post(reverse('clientes:criar'), {**DADOS, 'cpf': '111.111.111-11'})

    assert resposta.status_code == 200
    assert 'CPF inválido' in resposta.content.decode()
    assert not Cliente.objects.exists()


def test_cpf_existente_leva_a_ficha_com_aviso(client, operador):
    existente = ClienteFactory(cpf='52998224725')

    resposta = client.post(reverse('clientes:criar'), DADOS, follow=True)

    assert resposta.redirect_chain[-1][0] == reverse('clientes:detalhe', args=[existente.pk])
    assert 'Já existe um Cliente' in resposta.content.decode()
    assert Cliente.objects.count() == 1


def test_lista_oculta_parte_do_cpf(client, operador):
    ClienteFactory(cpf='52998224725')

    conteudo = client.get(reverse('clientes:lista')).content.decode()

    assert '529.982.247-25' not in conteudo
    assert '***.982.247-**' in conteudo


def test_operador_edita_e_inativa_e_reativa(client, operador):
    cliente = ClienteFactory()

    client.post(
        reverse('clientes:editar', args=[cliente.pk]),
        {'nome': 'Nome Novo', 'telefone': '123', 'email': ''},
    )
    client.post(reverse('clientes:inativar', args=[cliente.pk]))
    cliente.refresh_from_db()
    assert cliente.nome == 'Nome Novo'
    assert not cliente.ativo

    client.post(reverse('clientes:reativar', args=[cliente.pk]))
    cliente.refresh_from_db()
    assert cliente.ativo


def test_historico_so_aparece_para_supervisor(client, db):
    cliente = ClienteFactory()
    url = reverse('clientes:detalhe', args=[cliente.pk])

    client.force_login(_usuario('Operador'))
    assert 'Histórico de alterações' not in client.get(url).content.decode()

    client.force_login(_usuario('Supervisor'))
    assert 'Histórico de alterações' in client.get(url).content.decode()


def test_lista_filtra_pela_busca(client, operador):
    ClienteFactory(nome='José da Silva')
    ClienteFactory(nome='Maria Souza')

    conteudo = client.get(reverse('clientes:lista'), {'q': 'silva'}).content.decode()

    assert 'José da Silva' in conteudo
    assert 'Maria Souza' not in conteudo


def test_requisicao_htmx_devolve_so_a_tabela(client, operador):
    ClienteFactory(nome='José da Silva')

    resposta = client.get(reverse('clientes:lista'), headers={'HX-Request': 'true'})

    conteudo = resposta.content.decode()
    assert 'José da Silva' in conteudo
    assert '<html' not in conteudo


def test_lista_e_paginada(client, operador):
    for i in range(30):
        ClienteFactory(nome=f'Cliente {i:02d}', cpf=f'{i:011d}')

    pagina1 = client.get(reverse('clientes:lista')).content.decode()
    pagina2 = client.get(reverse('clientes:lista'), {'page': 2}).content.decode()

    assert 'Cliente 00' in pagina1
    assert 'Cliente 29' not in pagina1
    assert 'Cliente 29' in pagina2
