import datetime
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.urls import reverse

from bancos.models import Banco
from beneficios.models import Beneficio
from clientes.models import Cliente
from contratos.models import Contrato
from propostas.models import Modalidade, Proposta

User = get_user_model()


@pytest.fixture
def client_logado(client, db):
    client.force_login(User.objects.create_user(username='maria', password='x'))
    return client


@pytest.fixture
def banco(db):
    return Banco.objects.create(nome='Banco Alfa', codigo='001')


@pytest.fixture
def modalidade(db):
    return Modalidade.objects.create(nome='Novo')


@pytest.fixture
def cliente(db):
    return Cliente.objects.create(
        nome='Maria Santos',
        cpf='52998224725',
        data_nascimento='1960-01-01',
        telefone='11988887777',
    )


def _usuario_com_permissoes(username, *perm_codenames, grupo=None):
    user = User.objects.create_user(username=username, password='x')
    for codename in perm_codenames:
        perm = Permission.objects.get(codename=codename)
        user.user_permissions.add(perm)
    if grupo:
        g, _ = Group.objects.get_or_create(name=grupo)
        user.groups.add(g)
    return user


def test_pagina_inicial_usa_layout_base(client_logado):
    resposta = client_logado.get(reverse('inicio:index'))

    assert resposta.status_code == 200
    html = resposta.content.decode()
    assert '<html lang="pt-br">' in html
    assert 'bootstrap' in html
    assert 'htmx' in html
    assert 'Início' in html


def test_saudacao_usa_nome_completo(client, db):
    user = User.objects.create_user(
        username='maria', password='x', first_name='Maria', last_name='Silva'
    )
    client.force_login(user)

    html = client.get(reverse('inicio:index')).content.decode()

    assert 'Olá, Maria Silva!' in html
    assert 'Atualizar saudação' not in html


def test_saudacao_cai_para_username_sem_nome(client_logado):
    html = client_logado.get(reverse('inicio:index')).content.decode()

    assert 'Olá, maria!' in html


def test_pagina_inicial_sem_permissoes_nao_mostra_secoes(client_logado):
    resposta = client_logado.get(reverse('inicio:index'))

    assert resposta.status_code == 200
    html = resposta.content.decode()
    assert 'Buscar por CPF ou nome' not in html
    assert 'Propostas em andamento' not in html
    assert 'Contratos pendentes' not in html


def test_pagina_inicial_com_view_cliente_mostra_busca(client, db):
    user = _usuario_com_permissoes('operador_cliente', 'view_cliente')
    client.force_login(user)

    resposta = client.get(reverse('inicio:index'))
    assert resposta.status_code == 200
    html = resposta.content.decode()
    assert 'Buscar por CPF ou nome' in html
    assert 'hx-get' in html
    assert 'Propostas em andamento' not in html
    assert 'Contratos pendentes' not in html


def test_busca_cliente_htmx_retorna_resultados_com_cpf_mascarado_e_beneficios(client, cliente):
    Beneficio.objects.create(
        cliente=cliente, numero='1234567890', especie=Beneficio.Especie.APOSENTADORIA, ativo=True
    )
    Beneficio.objects.create(
        cliente=cliente, numero='0987654321', especie=Beneficio.Especie.PENSAO, ativo=False
    )
    user = _usuario_com_permissoes('operador_cliente', 'view_cliente')
    client.force_login(user)

    url = reverse('inicio:buscar_clientes')
    resposta = client.get(url, {'q': 'Maria'}, HTTP_HX_REQUEST='true')

    assert resposta.status_code == 200
    html = resposta.content.decode()
    assert 'Maria Santos' in html
    assert reverse('clientes:detalhe', kwargs={'pk': cliente.pk}) in html
    assert cliente.cpf_mascarado in html
    assert '52998224725' not in html
    assert '1 benefício ativo' in html


def test_busca_cliente_htmx_cpf_valido_inedito_com_add_cliente_mostra_botao(client, db):
    user = _usuario_com_permissoes('operador_cadastra', 'view_cliente', 'add_cliente')
    client.force_login(user)

    cpf_inedito = '15350946056'
    url = reverse('inicio:buscar_clientes')
    resposta = client.get(url, {'q': cpf_inedito}, HTTP_HX_REQUEST='true')

    assert resposta.status_code == 200
    html = resposta.content.decode()
    assert 'Cadastrar Cliente com este CPF' in html
    assert f'{reverse("clientes:criar")}?cpf={cpf_inedito}' in html


def test_busca_cliente_htmx_cpf_valido_inedito_sem_add_cliente_nao_mostra_botao(client, db):
    user = _usuario_com_permissoes('operador_so_ve', 'view_cliente')
    client.force_login(user)

    cpf_inedito = '15350946056'
    url = reverse('inicio:buscar_clientes')
    resposta = client.get(url, {'q': cpf_inedito}, HTTP_HX_REQUEST='true')

    assert resposta.status_code == 200
    html = resposta.content.decode()
    assert 'Cadastrar Cliente com este CPF' not in html
    assert 'Nenhum Cliente encontrado' in html


def test_busca_cliente_htmx_cpf_invalido_sem_resultado_nao_mostra_botao(client, db):
    user = _usuario_com_permissoes('operador_cadastra', 'view_cliente', 'add_cliente')
    client.force_login(user)

    url = reverse('inicio:buscar_clientes')
    resposta = client.get(url, {'q': '11111111111'}, HTTP_HX_REQUEST='true')

    assert resposta.status_code == 200
    html = resposta.content.decode()
    assert 'Cadastrar Cliente com este CPF' not in html
    assert 'Nenhum Cliente encontrado' in html


def test_busca_cliente_htmx_nome_sem_resultado_nao_mostra_botao(client, db):
    user = _usuario_com_permissoes('operador_cadastra', 'view_cliente', 'add_cliente')
    client.force_login(user)

    url = reverse('inicio:buscar_clientes')
    resposta = client.get(url, {'q': 'Nome Inexistente'}, HTTP_HX_REQUEST='true')

    assert resposta.status_code == 200
    html = resposta.content.decode()
    assert 'Cadastrar Cliente com este CPF' not in html
    assert 'Nenhum Cliente encontrado' in html


def test_busca_cliente_htmx_sem_permissao_retorna_403(client, db):
    user = _usuario_com_permissoes('sem_permissao')
    client.force_login(user)

    url = reverse('inicio:buscar_clientes')
    resposta = client.get(url, {'q': 'Maria'})
    assert resposta.status_code == 403


def test_fila_propostas_padrao_operador_e_minhas(client, cliente, banco, modalidade):
    operador1 = _usuario_com_permissoes('op1', 'view_proposta', grupo='Operador')
    operador2 = _usuario_com_permissoes('op2', 'view_proposta', grupo='Operador')
    beneficio = Beneficio.objects.create(
        cliente=cliente, numero='9999999999', especie=Beneficio.Especie.APOSENTADORIA
    )
    p_minha = Proposta.objects.create(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=operador1,
        status=Proposta.Status.DIGITADA,
        valor=Decimal('5000'),
        valor_liberado=Decimal('5000'),
        prazo=48,
        parcela=Decimal('150'),
        taxa=Decimal('1.8'),
    )
    p_outra = Proposta.objects.create(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=operador2,
        status=Proposta.Status.ENVIADA,
        valor=Decimal('6000'),
        valor_liberado=Decimal('6000'),
        prazo=48,
        parcela=Decimal('180'),
        taxa=Decimal('1.8'),
    )

    client.force_login(operador1)
    resposta = client.get(reverse('inicio:index'))
    assert resposta.status_code == 200
    html = resposta.content.decode()

    assert f'#{p_minha.pk}' in html
    assert f'#{p_outra.pk}' not in html
    assert 'Propostas em andamento' in html


def test_fila_propostas_padrao_supervisor_e_todas(client, cliente, banco, modalidade):
    supervisor = _usuario_com_permissoes('sup1', 'view_proposta', grupo='Supervisor')
    operador = _usuario_com_permissoes('op1', 'view_proposta', grupo='Operador')
    beneficio = Beneficio.objects.create(
        cliente=cliente, numero='8888888888', especie=Beneficio.Especie.APOSENTADORIA
    )
    p_sup = Proposta.objects.create(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=supervisor,
        status=Proposta.Status.DIGITADA,
        valor=Decimal('5000'),
        valor_liberado=Decimal('5000'),
        prazo=48,
        parcela=Decimal('150'),
        taxa=Decimal('1.8'),
    )
    p_op = Proposta.objects.create(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=operador,
        status=Proposta.Status.ENVIADA,
        valor=Decimal('6000'),
        valor_liberado=Decimal('6000'),
        prazo=48,
        parcela=Decimal('180'),
        taxa=Decimal('1.8'),
    )

    client.force_login(supervisor)
    resposta = client.get(reverse('inicio:index'))
    assert resposta.status_code == 200
    html = resposta.content.decode()

    assert f'#{p_sup.pk}' in html
    assert f'#{p_op.pk}' in html


def test_fila_propostas_alternancia_via_query_string_e_htmx(client, cliente, banco, modalidade):
    operador1 = _usuario_com_permissoes('op1', 'view_proposta', grupo='Operador')
    operador2 = _usuario_com_permissoes('op2', 'view_proposta', grupo='Operador')
    beneficio = Beneficio.objects.create(
        cliente=cliente, numero='7777777777', especie=Beneficio.Especie.APOSENTADORIA
    )
    p_minha = Proposta.objects.create(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=operador1,
        status=Proposta.Status.DIGITADA,
        valor=Decimal('5000'),
        valor_liberado=Decimal('5000'),
        prazo=48,
        parcela=Decimal('150'),
        taxa=Decimal('1.8'),
    )
    p_outra = Proposta.objects.create(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=operador2,
        status=Proposta.Status.ENVIADA,
        valor=Decimal('6000'),
        valor_liberado=Decimal('6000'),
        prazo=48,
        parcela=Decimal('180'),
        taxa=Decimal('1.8'),
    )

    client.force_login(operador1)
    # Alterna via query string na página inteira
    resposta_qs = client.get(reverse('inicio:index') + '?propostas=todas')
    assert resposta_qs.status_code == 200
    html_qs = resposta_qs.content.decode()
    assert f'#{p_minha.pk}' in html_qs
    assert f'#{p_outra.pk}' in html_qs

    # Alterna via HTMX na rota parcial
    resposta_htmx = client.get(
        reverse('inicio:fila_propostas') + '?propostas=todas', HTTP_HX_REQUEST='true'
    )
    assert resposta_htmx.status_code == 200
    html_htmx = resposta_htmx.content.decode()
    assert f'#{p_minha.pk}' in html_htmx
    assert f'#{p_outra.pk}' in html_htmx


def test_fila_propostas_destaca_digitada_e_aprovada(client, cliente, banco, modalidade):
    operador = _usuario_com_permissoes('op1', 'view_proposta', grupo='Supervisor')
    beneficio = Beneficio.objects.create(
        cliente=cliente, numero='6666666666', especie=Beneficio.Especie.APOSENTADORIA
    )
    Proposta.objects.create(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=operador,
        status=Proposta.Status.DIGITADA,
        valor=Decimal('5000'),
        valor_liberado=Decimal('5000'),
        prazo=48,
        parcela=Decimal('150'),
        taxa=Decimal('1.8'),
    )
    Proposta.objects.create(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=operador,
        status=Proposta.Status.ENVIADA,
        valor=Decimal('5000'),
        valor_liberado=Decimal('5000'),
        prazo=48,
        parcela=Decimal('150'),
        taxa=Decimal('1.8'),
    )
    Proposta.objects.create(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=operador,
        status=Proposta.Status.APROVADA,
        valor=Decimal('5000'),
        valor_liberado=Decimal('5000'),
        prazo=48,
        parcela=Decimal('150'),
        taxa=Decimal('1.8'),
    )

    client.force_login(operador)
    resposta = client.get(reverse('inicio:index'))
    assert resposta.status_code == 200
    html = resposta.content.decode()

    # Digitada e Aprovada devem ter destaque visual (ex: badge text-bg-warning ou similar)
    assert 'badge' in html
    assert 'text-bg-warning' in html or 'bg-warning' in html


def test_fila_contratos_exibe_formalizado_e_averbado_e_links(client, cliente, banco, modalidade):
    user = _usuario_com_permissoes('op_contratos', 'view_contrato')
    beneficio = Beneficio.objects.create(
        cliente=cliente, numero='5555555556', especie=Beneficio.Especie.APOSENTADORIA
    )
    p1 = Proposta.objects.create(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=user,
        status=Proposta.Status.FORMALIZADA,
        valor=Decimal('5000'),
        valor_liberado=Decimal('5000'),
        prazo=48,
        parcela=Decimal('150'),
        taxa=Decimal('1.8'),
    )
    p2 = Proposta.objects.create(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=user,
        status=Proposta.Status.FORMALIZADA,
        valor=Decimal('6000'),
        valor_liberado=Decimal('6000'),
        prazo=48,
        parcela=Decimal('180'),
        taxa=Decimal('1.8'),
    )
    p3 = Proposta.objects.create(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=user,
        status=Proposta.Status.FORMALIZADA,
        valor=Decimal('7000'),
        valor_liberado=Decimal('7000'),
        prazo=48,
        parcela=Decimal('200'),
        taxa=Decimal('1.8'),
    )

    c_formalizado = Contrato.objects.create(
        proposta=p1,
        modalidade=modalidade,
        status=Contrato.Status.FORMALIZADO,
        valor=p1.valor,
        valor_liberado=p1.valor_liberado,
        prazo=p1.prazo,
        parcela=p1.parcela,
        taxa=p1.taxa,
    )
    c_averbado = Contrato.objects.create(
        proposta=p2,
        modalidade=modalidade,
        status=Contrato.Status.AVERBADO,
        valor=p2.valor,
        valor_liberado=p2.valor_liberado,
        prazo=p2.prazo,
        parcela=p2.parcela,
        taxa=p2.taxa,
    )
    c_pago = Contrato.objects.create(
        proposta=p3,
        modalidade=modalidade,
        status=Contrato.Status.PAGO,
        valor=p3.valor,
        valor_liberado=p3.valor_liberado,
        prazo=p3.prazo,
        parcela=p3.parcela,
        taxa=p3.taxa,
        data_pagamento=datetime.date.today(),
    )

    client.force_login(user)
    resposta = client.get(reverse('inicio:index'))
    assert resposta.status_code == 200
    html = resposta.content.decode()

    assert 'Contratos pendentes' in html
    assert f'#{c_formalizado.pk}' in html
    assert f'#{c_averbado.pk}' in html
    assert f'#{c_pago.pk}' not in html
    assert reverse('contratos:detalhe', kwargs={'pk': c_formalizado.pk}) in html
    assert reverse('clientes:detalhe', kwargs={'pk': cliente.pk}) in html


def test_fila_contratos_oculta_sem_permissao(client_logado):
    resposta = client_logado.get(reverse('inicio:index'))
    assert resposta.status_code == 200
    html = resposta.content.decode()
    assert 'Contratos pendentes' not in html
