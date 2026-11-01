import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse

from core.navegacao import _iniciais


def _usuario(permissoes=(), **extra):
    user = get_user_model().objects.create_user(username='maria', password='x', **extra)
    for codigo in permissoes:
        app, nome = codigo.split('.')
        permissao = Permission.objects.get(content_type__app_label=app, codename=nome)
        user.user_permissions.add(permissao)
    return user


def _menu(html):
    return html.split('id="menu-lateral"')[1].split('</aside>')[0]


@pytest.mark.django_db
def test_sidebar_mostra_so_itens_permitidos_na_ordem_do_fluxo(client):
    client.force_login(_usuario(['bancos.view_banco', 'clientes.view_cliente']))

    menu = _menu(client.get(reverse('inicio:index')).content.decode())

    assert menu.index('Clientes') < menu.index('Bancos')
    assert 'Cadastros' in menu
    assert 'Processos' not in menu
    assert 'Propostas' not in menu
    assert 'Contratos' not in menu
    assert 'Benefícios' not in menu


@pytest.mark.django_db
def test_item_da_area_atual_fica_ativo(client):
    client.force_login(_usuario(['bancos.view_banco', 'clientes.view_cliente']))

    menu = _menu(client.get(reverse('bancos:lista')).content.decode())

    assert f'class="menu-link ativo" href="{reverse("bancos:lista")}" aria-current="page"' in menu
    assert f'class="menu-link" href="{reverse("clientes:lista")}">' in menu


@pytest.mark.django_db
def test_link_de_admin_so_para_staff(client):
    client.force_login(_usuario())
    assert 'Administração' not in client.get(reverse('inicio:index')).content.decode()

    client.logout()
    get_user_model().objects.all().delete()
    client.force_login(_usuario(is_staff=True))
    assert 'Administração' in client.get(reverse('inicio:index')).content.decode()


@pytest.mark.django_db
def test_login_nao_tem_sidebar(client):
    html = client.get(reverse('accounts:login')).content.decode()

    assert 'id="menu-lateral"' not in html


@pytest.mark.django_db
def test_barra_superior_mostra_nome_do_operador(client):
    client.force_login(_usuario(first_name='Maria', last_name='Silva'))

    html = client.get(reverse('inicio:index')).content.decode()

    assert 'id="nome-operador">Maria Silva<' in html
    assert '>MS</span>' in html


@pytest.mark.django_db
def test_pagina_403_mantem_sidebar(client):
    client.force_login(_usuario())

    resposta = client.get(reverse('bancos:lista'))

    assert resposta.status_code == 403
    assert 'id="menu-lateral"' in resposta.content.decode()


@pytest.mark.django_db
def test_itens_ficam_nos_grupos_cadastros_e_processos(client):
    client.force_login(
        _usuario(
            [
                'clientes.view_cliente',
                'bancos.view_banco',
                'propostas.view_proposta',
                'contratos.view_contrato',
            ]
        )
    )

    menu = _menu(client.get(reverse('inicio:index')).content.decode())

    cadastros, processos = menu.index('Cadastros'), menu.index('Processos')
    assert cadastros < menu.index('Clientes') < menu.index('Bancos') < processos
    assert processos < menu.index('Propostas') < menu.index('Contratos')


@pytest.mark.django_db
def test_botao_para_recolher_sidebar_e_script_no_head(client):
    client.force_login(_usuario())

    html = client.get(reverse('inicio:index')).content.decode()

    assert 'id="botao-menu"' in html
    assert 'menu.js' in html.split('</head>')[0]


@pytest.mark.django_db
def test_grupos_da_sidebar_sao_recolhiveis(client):
    client.force_login(_usuario(['clientes.view_cliente']))

    menu = _menu(client.get(reverse('inicio:index')).content.decode())

    assert 'data-bs-target="#grupo-cadastros"' in menu
    assert 'id="grupo-cadastros" class="collapse show' in menu


@pytest.mark.django_db
def test_tema_admin_e_sair_ficam_no_menu_do_usuario(client):
    client.force_login(_usuario(is_staff=True))

    html = client.get(reverse('inicio:index')).content.decode()
    dropdown = html.split('class="dropdown-menu')[1].split('</ul>')[0]

    for trecho in ('id="botao-tema"', 'Administração', 'Sair'):
        assert trecho in dropdown
    assert 'Administração' not in _menu(html)


def test_iniciais_do_operador():
    assert _iniciais('Maria da Silva') == 'MS'
    assert _iniciais('maria') == 'MA'


@pytest.mark.django_db
def test_layout_css_carrega_depois_do_tema(client):
    client.force_login(_usuario())

    head = client.get(reverse('inicio:index')).content.decode().split('</head>')[0]

    assert head.index('tema.css') < head.index('layout.css')
