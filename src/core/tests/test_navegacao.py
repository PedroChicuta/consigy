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


def _breadcrumb(html):
    return html.split('<ol class="breadcrumb')[1].split('</ol>')[0]


@pytest.mark.django_db
def test_breadcrumbs_em_clientes_e_beneficios(client):
    from beneficios.tests.factories import BeneficioFactory

    beneficio = BeneficioFactory(cliente__nome='Maria Silva', numero='2048112233')
    cliente = beneficio.cliente
    client.force_login(
        _usuario(
            [
                'clientes.view_cliente',
                'clientes.add_cliente',
                'clientes.change_cliente',
                'beneficios.view_beneficio',
                'beneficios.add_beneficio',
            ]
        )
    )
    url_clientes = reverse('clientes:lista')
    url_cliente = reverse('clientes:detalhe', args=[cliente.pk])

    trilha_cliente = _breadcrumb(client.get(url_cliente).content.decode())
    assert f'<a href="{url_clientes}">Clientes</a>' in trilha_cliente
    assert 'aria-current="page">Maria Silva</li>' in trilha_cliente

    trilha_novo_cliente = _breadcrumb(client.get(reverse('clientes:criar')).content.decode())
    assert f'<a href="{url_clientes}">Clientes</a>' in trilha_novo_cliente
    assert 'aria-current="page">Novo Cliente</li>' in trilha_novo_cliente

    trilha_editar_cliente = _breadcrumb(
        client.get(reverse('clientes:editar', args=[cliente.pk])).content.decode()
    )
    assert f'<a href="{url_clientes}">Clientes</a>' in trilha_editar_cliente
    assert f'<a href="{url_cliente}">Maria Silva</a>' in trilha_editar_cliente
    assert 'Editar' in trilha_editar_cliente

    trilha_beneficio = _breadcrumb(
        client.get(reverse('beneficios:detalhe', args=[beneficio.pk])).content.decode()
    )
    assert f'<a href="{url_clientes}">Clientes</a>' in trilha_beneficio
    assert f'<a href="{url_cliente}">Maria Silva</a>' in trilha_beneficio
    assert 'aria-current="page">Benefício 2048112233</li>' in trilha_beneficio

    trilha_novo_beneficio = _breadcrumb(
        client.get(reverse('beneficios:criar', args=[cliente.pk])).content.decode()
    )
    assert f'<a href="{url_clientes}">Clientes</a>' in trilha_novo_beneficio
    assert f'<a href="{url_cliente}">Maria Silva</a>' in trilha_novo_beneficio
    assert 'aria-current="page">Novo Benefício</li>' in trilha_novo_beneficio


@pytest.mark.django_db
def test_breadcrumbs_em_bancos_propostas_e_contratos(client):
    from bancos.tests.factories import BancoFactory
    from contratos.tests.factories import ContratoFactory
    from propostas.tests.factories import PropostaFactory

    banco = BancoFactory(nome='Banco Alfa')
    proposta = PropostaFactory()
    contrato = ContratoFactory()
    client.force_login(
        _usuario(
            [
                'bancos.view_banco',
                'bancos.add_banco',
                'bancos.change_banco',
                'propostas.view_proposta',
                'propostas.add_proposta',
                'propostas.change_proposta',
                'contratos.view_contrato',
            ]
        )
    )
    url_bancos = reverse('bancos:lista')
    url_propostas = reverse('propostas:lista')
    url_proposta = reverse('propostas:detalhe', args=[proposta.pk])
    url_contratos = reverse('contratos:lista')

    trilha_novo_banco = _breadcrumb(client.get(reverse('bancos:criar')).content.decode())
    assert f'<a href="{url_bancos}">Bancos</a>' in trilha_novo_banco
    assert 'aria-current="page">Novo Banco</li>' in trilha_novo_banco

    trilha_editar_banco = _breadcrumb(
        client.get(reverse('bancos:editar', args=[banco.pk])).content.decode()
    )
    assert f'<a href="{url_bancos}">Bancos</a>' in trilha_editar_banco
    assert 'aria-current="page">Editar Banco Alfa</li>' in trilha_editar_banco

    trilha_proposta = _breadcrumb(client.get(url_proposta).content.decode())
    assert f'<a href="{url_propostas}">Propostas</a>' in trilha_proposta
    assert f'aria-current="page">Proposta {proposta.pk}</li>' in trilha_proposta

    trilha_nova_proposta = _breadcrumb(client.get(reverse('propostas:criar')).content.decode())
    assert f'<a href="{url_propostas}">Propostas</a>' in trilha_nova_proposta
    assert 'aria-current="page">Nova Proposta</li>' in trilha_nova_proposta

    trilha_editar_proposta = _breadcrumb(
        client.get(reverse('propostas:editar', args=[proposta.pk])).content.decode()
    )
    assert f'<a href="{url_propostas}">Propostas</a>' in trilha_editar_proposta
    assert f'<a href="{url_proposta}">Proposta {proposta.pk}</a>' in trilha_editar_proposta
    assert 'Editar' in trilha_editar_proposta

    trilha_contrato = _breadcrumb(
        client.get(reverse('contratos:detalhe', args=[contrato.pk])).content.decode()
    )
    assert f'<a href="{url_contratos}">Contratos</a>' in trilha_contrato
    assert f'aria-current="page">Contrato {contrato.pk}</li>' in trilha_contrato


@pytest.mark.django_db
def test_links_de_ficha_propagam_next_e_cancelar_retorna_a_origem(client):
    from propostas.tests.factories import PropostaFactory

    proposta = PropostaFactory()
    cliente = proposta.beneficio.cliente
    client.force_login(
        _usuario(
            [
                'clientes.view_cliente',
                'clientes.change_cliente',
                'beneficios.add_beneficio',
                'propostas.view_proposta',
                'propostas.add_proposta',
                'propostas.change_proposta',
            ]
        )
    )
    url_cliente = reverse('clientes:detalhe', args=[cliente.pk])
    ficha_cliente = client.get(url_cliente).content.decode()

    url_editar_cliente = f'{reverse("clientes:editar", args=[cliente.pk])}?next={url_cliente}'
    url_novo_beneficio = f'{reverse("beneficios:criar", args=[cliente.pk])}?next={url_cliente}'
    url_nova_proposta = f'{reverse("propostas:criar")}?next={url_cliente}'

    assert f'href="{url_editar_cliente}"' in ficha_cliente
    assert f'href="{url_novo_beneficio}"' in ficha_cliente
    assert f'href="{url_nova_proposta}"' in ficha_cliente

    for url_form in (url_editar_cliente, url_novo_beneficio, url_nova_proposta):
        html_form = client.get(url_form).content.decode()
        assert f'href="{url_cliente}">Cancelar</a>' in html_form

    url_proposta = reverse('propostas:detalhe', args=[proposta.pk])
    ficha_proposta = client.get(url_proposta).content.decode()
    url_editar_proposta = f'{reverse("propostas:editar", args=[proposta.pk])}?next={url_proposta}'
    assert f'href="{url_editar_proposta}"' in ficha_proposta

    html_editar_proposta_do_cliente = client.get(
        reverse('propostas:editar', args=[proposta.pk]), {'next': url_cliente}
    ).content.decode()
    assert f'href="{url_cliente}">Cancelar</a>' in html_editar_proposta_do_cliente


def test_componente_breadcrumb_aceita_lista_no_contexto():
    from django.template import Context, Template

    tpl = Template("{% include 'componentes/_breadcrumb.html' %}")
    html = tpl.render(
        Context(
            {
                'breadcrumbs': [
                    ('Clientes', '/clientes/'),
                    ('Maria Silva', '/clientes/1/'),
                    ('Benefício 2048112233', None),
                ]
            }
        )
    )

    assert '<a href="/clientes/">Clientes</a>' in html
    assert '<a href="/clientes/1/">Maria Silva</a>' in html
    assert 'aria-current="page">Benefício 2048112233</li>' in html


