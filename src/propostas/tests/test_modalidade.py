import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.urls import reverse

from bancos.tests.factories import BancoFactory
from beneficios.tests.factories import BeneficioFactory
from propostas import selectors, services
from propostas.exceptions import (
    ModalidadeInativa,
    ModalidadeJaAtiva,
    ModalidadeJaInativa,
    NomeDeModalidadeDuplicado,
    NomeDeModalidadeObrigatorio,
)
from propostas.forms import PropostaForm
from propostas.models import Modalidade, Proposta
from propostas.tests.factories import ModalidadeFactory, PropostaFactory, UsuarioFactory

CONDICOES = {'valor': 1000, 'valor_liberado': 900, 'prazo': 12, 'parcela': 100, 'taxa': 1}


def _usuario(grupo, username, staff=True):
    usuario = get_user_model().objects.create_user(username=username, password='x', is_staff=staff)
    usuario.groups.add(Group.objects.get(name=grupo))
    return usuario


def test_migration_cria_modalidades_iniciais(db):
    nomes = dict(Modalidade.objects.values_list('nome', 'envolve_portabilidade'))

    assert nomes == {
        'Consignado novo': False,
        'Portabilidade + refinanciamento': True,
        'Cartão com saque': False,
    }


def test_criar_modalidade_nasce_ativa_limpa_espacos_e_grava_historico(db):
    usuario = UsuarioFactory()

    modalidade = services.criar_modalidade(
        usuario=usuario, nome='  Refinanciamento  ', envolve_portabilidade=True
    )

    salva = Modalidade.objects.get(pk=modalidade.pk)
    assert salva.nome == 'Refinanciamento'
    assert salva.ativo is True
    assert salva.envolve_portabilidade is True
    assert salva.history.first().history_user == usuario
    assert salva in selectors.modalidades_ativas()
    assert salva in selectors.listar_modalidades()


def test_criar_modalidade_rejeita_nome_vazio_ou_duplicado(db):
    usuario = UsuarioFactory()
    total_inicial = Modalidade.objects.count()

    with pytest.raises(NomeDeModalidadeObrigatorio):
        services.criar_modalidade(usuario=usuario, nome='   ')

    with pytest.raises(NomeDeModalidadeDuplicado):
        services.criar_modalidade(usuario=usuario, nome='  consignado novo  ')

    with pytest.raises(NomeDeModalidadeDuplicado):
        services.criar_modalidade(usuario=usuario, nome='CARTÃO COM SAQUE')

    assert Modalidade.objects.count() == total_inicial


def test_editar_modalidade_altera_nome_portabilidade_e_grava_historico(db):
    criador = UsuarioFactory()
    editor = UsuarioFactory()
    modalidade = services.criar_modalidade(
        usuario=criador, nome='Portabilidade Pura', envolve_portabilidade=False
    )

    services.editar_modalidade(
        usuario=editor,
        modalidade=modalidade,
        nome='  Portabilidade Pura  ',
        envolve_portabilidade=True,
    )

    modalidade.refresh_from_db()
    assert modalidade.nome == 'Portabilidade Pura'
    assert modalidade.envolve_portabilidade is True
    assert modalidade.history.count() == 2
    assert modalidade.history.first().history_user == editor


def test_editar_modalidade_rejeita_nome_de_outra(db):
    usuario = UsuarioFactory()
    modalidade = ModalidadeFactory(nome='Outra Modalidade')

    with pytest.raises(NomeDeModalidadeDuplicado):
        services.editar_modalidade(
            usuario=usuario,
            modalidade=modalidade,
            nome='  consignado novo ',
            envolve_portabilidade=False,
        )

    modalidade.refresh_from_db()
    assert modalidade.nome == 'Outra Modalidade'


def test_inativar_e_reativar_modalidade_registra_historico_e_preserva_existentes(db):
    from contratos.tests.factories import ContratoFactory

    autor_inativacao = UsuarioFactory()
    autor_reativacao = UsuarioFactory()
    modalidade = ModalidadeFactory(nome='Saque Aniversário')
    contrato = ContratoFactory(proposta__modalidade=modalidade)
    proposta = contrato.proposta

    services.inativar_modalidade(usuario=autor_inativacao, modalidade=modalidade)
    modalidade.refresh_from_db()
    assert modalidade.ativo is False
    assert modalidade.history.first().history_user == autor_inativacao
    assert modalidade not in selectors.modalidades_ativas()
    assert modalidade in selectors.listar_modalidades()
    assert modalidade not in PropostaForm().fields['modalidade'].queryset

    proposta.refresh_from_db()
    contrato.refresh_from_db()
    assert proposta.modalidade == modalidade
    assert contrato.modalidade == modalidade

    with pytest.raises(ModalidadeJaInativa):
        services.inativar_modalidade(usuario=autor_inativacao, modalidade=modalidade)

    services.reativar_modalidade(usuario=autor_reativacao, modalidade=modalidade)
    modalidade.refresh_from_db()
    assert modalidade.ativo is True
    assert modalidade.history.first().history_user == autor_reativacao
    assert modalidade in selectors.modalidades_ativas()

    with pytest.raises(ModalidadeJaAtiva):
        services.reativar_modalidade(usuario=autor_reativacao, modalidade=modalidade)


def test_nome_duplicado_e_rejeitado(db):
    with pytest.raises(IntegrityError), transaction.atomic():
        Modalidade.objects.create(nome='Consignado novo')


def test_modalidade_com_proposta_nao_pode_ser_apagada(db):
    proposta = PropostaFactory()

    with pytest.raises(ProtectedError):
        proposta.modalidade.delete()


def test_proposta_exige_modalidade(db):
    modelo = PropostaFactory()

    with pytest.raises(IntegrityError), transaction.atomic():
        Proposta.objects.create(
            beneficio=modelo.beneficio,
            banco=modelo.banco,
            operador=modelo.operador,
            modalidade=None,
            **CONDICOES,
        )


def test_form_so_oferece_modalidades_ativas(db):
    inativa = ModalidadeFactory(ativo=False)

    ids = PropostaForm().fields['modalidade'].queryset.values_list('pk', flat=True)

    assert inativa.pk not in ids
    assert Modalidade.objects.get(nome='Consignado novo').pk in ids


def test_form_de_edicao_mantem_modalidade_inativada_depois(db):
    proposta = PropostaFactory()
    proposta.modalidade.ativo = False
    proposta.modalidade.save()

    ids = PropostaForm(proposta=proposta).fields['modalidade'].queryset
    assert proposta.modalidade in ids


def test_form_sem_modalidade_e_invalido(db):
    form = PropostaForm(
        data={'valor': '1', 'valor_liberado': '1', 'prazo': '1', 'parcela': '1', 'taxa': '1'}
    )

    assert not form.is_valid()
    assert 'modalidade' in form.errors


def test_service_nao_cria_com_modalidade_inativa(db):
    with pytest.raises(ModalidadeInativa):
        services.criar_proposta(
            usuario=UsuarioFactory(),
            beneficio=BeneficioFactory(),
            banco=BancoFactory(),
            modalidade=ModalidadeFactory(ativo=False),
            **CONDICOES,
        )


def test_edicao_mantem_modalidade_inativada_mas_nao_troca_para_inativa(db):
    proposta = PropostaFactory()
    proposta.modalidade.ativo = False
    proposta.modalidade.save()
    dados = {'beneficio': proposta.beneficio, 'banco': proposta.banco, **CONDICOES}

    services.editar_proposta(
        usuario=UsuarioFactory(), proposta=proposta, modalidade=proposta.modalidade, **dados
    )
    with pytest.raises(ModalidadeInativa):
        services.editar_proposta(
            usuario=UsuarioFactory(),
            proposta=proposta,
            modalidade=ModalidadeFactory(ativo=False),
            **dados,
        )


def test_modalidade_aparece_na_lista_e_no_detalhe(client, db):
    client.force_login(_usuario('Operador', 'op', staff=False))
    proposta = PropostaFactory(modalidade=ModalidadeFactory(nome='Modalidade Visível'))

    lista = client.get(reverse('propostas:lista'))
    detalhe = client.get(reverse('propostas:detalhe', args=[proposta.pk]))

    assert 'Modalidade Visível' in lista.content.decode()
    assert 'Modalidade Visível' in detalhe.content.decode()


def test_operador_sem_permissao_recebe_403_nas_rotas_de_modalidades(client, db):
    modalidade = ModalidadeFactory(nome='Original')
    client.force_login(_usuario('Operador', 'op', staff=False))

    assert client.get(reverse('modalidades:lista')).status_code == 403
    assert client.get(reverse('modalidades:criar')).status_code == 403
    assert client.post(reverse('modalidades:criar'), {'nome': 'X'}).status_code == 403
    assert client.get(reverse('modalidades:editar', args=[modalidade.pk])).status_code == 403
    assert (
        client.post(reverse('modalidades:editar', args=[modalidade.pk]), {'nome': 'X'}).status_code
        == 403
    )
    assert client.post(reverse('modalidades:inativar', args=[modalidade.pk])).status_code == 403
    assert client.post(reverse('modalidades:reativar', args=[modalidade.pk])).status_code == 403

    modalidade.refresh_from_db()
    assert modalidade.nome == 'Original'
    assert modalidade.ativo is True


def test_usuario_so_com_view_modalidade_ve_listagem_sem_acoes_de_alteracao(client, db):
    from django.contrib.auth.models import Permission

    leitor = get_user_model().objects.create_user(username='leitor', password='x')
    leitor.user_permissions.add(
        Permission.objects.get(content_type__app_label='propostas', codename='view_modalidade')
    )
    inativa = ModalidadeFactory(nome='Modalidade Inativa', ativo=False, envolve_portabilidade=True)
    client.force_login(leitor)

    conteudo = client.get(reverse('modalidades:lista')).content.decode()

    assert 'Consignado novo' in conteudo
    assert 'Modalidade Inativa' in conteudo
    assert 'Sim' in conteudo
    assert 'Não' in conteudo
    assert 'Ativa' in conteudo
    assert 'Inativa' in conteudo
    assert 'Nova Modalidade' not in conteudo
    assert reverse('modalidades:editar', args=[inativa.pk]) not in conteudo
    assert reverse('modalidades:reativar', args=[inativa.pk]) not in conteudo


def test_supervisor_cria_edita_inativa_e_reativa_modalidade_pela_interface(client, db):
    supervisor = _usuario('Supervisor', 'sup', staff=False)
    client.force_login(supervisor)

    resposta_criar = client.post(
        reverse('modalidades:criar'),
        {'nome': '  Portabilidade Pura  ', 'envolve_portabilidade': 'on'},
        follow=True,
    )
    assert 'Modalidade cadastrada.' in resposta_criar.content.decode()
    modalidade = Modalidade.objects.get(nome='Portabilidade Pura')
    assert modalidade.envolve_portabilidade is True
    assert modalidade.ativo is True

    resposta_editar = client.post(
        reverse('modalidades:editar', args=[modalidade.pk]),
        {'nome': 'Refinanciamento Puro'},
        follow=True,
    )
    assert 'Modalidade atualizada.' in resposta_editar.content.decode()
    modalidade.refresh_from_db()
    assert modalidade.nome == 'Refinanciamento Puro'
    assert modalidade.envolve_portabilidade is False

    resposta_inativar = client.post(
        reverse('modalidades:inativar', args=[modalidade.pk]), follow=True
    )
    assert 'Modalidade inativada.' in resposta_inativar.content.decode()
    modalidade.refresh_from_db()
    assert modalidade.ativo is False

    resposta_reativar = client.post(
        reverse('modalidades:reativar', args=[modalidade.pk]), follow=True
    )
    assert 'Modalidade reativada.' in resposta_reativar.content.decode()
    modalidade.refresh_from_db()
    assert modalidade.ativo is True

    registros = list(modalidade.history.all())
    assert len(registros) == 4
    assert all(r.history_user == supervisor for r in registros)


def test_nome_duplicado_mostra_erro_amigavel_no_formulario_de_criacao_e_edicao(client, db):
    supervisor = _usuario('Supervisor', 'sup', staff=False)
    client.force_login(supervisor)
    outra = ModalidadeFactory(nome='Outra Modalidade')

    resposta_criar = client.post(reverse('modalidades:criar'), {'nome': '  consignado novo  '})
    assert resposta_criar.status_code == 200
    assert 'Já existe uma Modalidade com este nome.' in resposta_criar.content.decode()

    resposta_editar = client.post(
        reverse('modalidades:editar', args=[outra.pk]),
        {'nome': '  CONSIGNADO NOVO  '},
    )
    assert resposta_editar.status_code == 200
    assert 'Já existe uma Modalidade com este nome.' in resposta_editar.content.decode()
    outra.refresh_from_db()
    assert outra.nome == 'Outra Modalidade'


def test_formularios_de_modalidade_exibem_breadcrumb_e_respeitam_retorno_contextual(client, db):
    supervisor = _usuario('Supervisor', 'sup', staff=False)
    client.force_login(supervisor)
    modalidade = ModalidadeFactory(nome='Cartão Benefício')
    url_lista = reverse('modalidades:lista')

    html_criar = client.get(reverse('modalidades:criar')).content.decode()
    trilha_criar = html_criar.split('<ol class="breadcrumb')[1].split('</ol>')[0]
    assert f'<a href="{url_lista}">Modalidades</a>' in trilha_criar
    assert 'aria-current="page">Nova Modalidade</li>' in trilha_criar
    assert f'href="{url_lista}">Cancelar</a>' in html_criar

    html_editar = client.get(reverse('modalidades:editar', args=[modalidade.pk])).content.decode()
    trilha_editar = html_editar.split('<ol class="breadcrumb')[1].split('</ol>')[0]
    assert f'<a href="{url_lista}">Modalidades</a>' in trilha_editar
    assert 'aria-current="page">Editar Cartão Benefício</li>' in trilha_editar
    assert f'href="{url_lista}">Cancelar</a>' in html_editar

    html_next_seguro = client.get(
        reverse('modalidades:criar'), {'next': '/propostas/nova/'}
    ).content.decode()
    assert 'href="/propostas/nova/">Cancelar</a>' in html_next_seguro

    html_pos_erro = client.post(
        reverse('modalidades:criar'), {'nome': '', 'next': '/propostas/nova/'}
    ).content.decode()
    assert 'href="/propostas/nova/">Cancelar</a>' in html_pos_erro

    html_next_externo = client.get(
        reverse('modalidades:editar', args=[modalidade.pk]),
        {'next': 'https://malicioso.exemplo/roubo'},
    ).content.decode()
    assert f'href="{url_lista}">Cancelar</a>' in html_next_externo
    assert 'malicioso' not in html_next_externo


def test_modalidade_nao_fica_registrada_no_admin():
    from django.contrib import admin

    assert Modalidade not in admin.site._registry
