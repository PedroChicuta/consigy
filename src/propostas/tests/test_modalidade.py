import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.urls import reverse

from bancos.tests.factories import BancoFactory
from beneficios.tests.factories import BeneficioFactory
from propostas import services
from propostas.exceptions import ModalidadeInativa
from propostas.forms import PropostaForm
from propostas.models import Modalidade, Proposta
from propostas.tests.factories import ModalidadeFactory, PropostaFactory, UsuarioFactory

CONDICOES = {'valor': 1000, 'prazo': 12, 'parcela': 100, 'taxa': 1}


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
    form = PropostaForm(data={'valor': '1', 'prazo': '1', 'parcela': '1', 'taxa': '1'})

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


def test_supervisor_gerencia_modalidade_no_admin_e_historico_registra_usuario(client, db):
    supervisor = _usuario('Supervisor', 'sup')
    client.force_login(supervisor)

    resposta = client.post(
        reverse('admin:propostas_modalidade_add'),
        {'nome': 'Nova', 'ativo': 'on', 'envolve_portabilidade': ''},
    )
    nova = Modalidade.objects.get(nome='Nova')
    client.post(
        reverse('admin:propostas_modalidade_change', args=[nova.pk]),
        {'nome': 'Nova', 'envolve_portabilidade': ''},
    )

    nova.refresh_from_db()
    assert resposta.status_code == 302
    assert nova.ativo is False
    assert nova.history.first().history_user == supervisor


def test_operador_nao_acessa_cadastro_de_modalidade(client, db):
    client.force_login(_usuario('Operador', 'op'))

    resposta = client.get(reverse('admin:propostas_modalidade_changelist'))

    assert resposta.status_code == 403


def test_admin_bloqueia_apagar_modalidade_com_proposta(client, db):
    client.force_login(_usuario('Supervisor', 'sup'))
    proposta = PropostaFactory()

    resposta = client.post(
        reverse('admin:propostas_modalidade_delete', args=[proposta.modalidade.pk]),
        {'post': 'yes'},
    )

    assert Modalidade.objects.filter(pk=proposta.modalidade.pk).exists()
    assert resposta.status_code in (200, 403)
