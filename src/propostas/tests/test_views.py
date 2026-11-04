import datetime
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from bancos.tests.factories import BancoFactory
from beneficios.tests.factories import BeneficioFactory, MargemFactory
from propostas.models import Proposta
from propostas.tests.factories import ModalidadeFactory, PropostaFactory

DADOS = {
    'valor': '9000.00',
    'valor_liberado': '8500.00',
    'prazo': '60',
    'parcela': '200.00',
    'taxa': '1.5000',
}


@pytest.fixture
def operador(client, db):
    usuario = get_user_model().objects.create_user(username='operador', password='x')
    usuario.groups.add(Group.objects.get(name='Operador'))
    client.force_login(usuario)
    return usuario


def test_sem_permissao_e_barrado(client, db):
    client.force_login(get_user_model().objects.create_user(username='sem', password='x'))

    assert client.get(reverse('propostas:lista')).status_code == 403
    assert client.get(reverse('propostas:criar')).status_code == 403


def test_operador_cria_proposta(client, operador):
    beneficio, banco = BeneficioFactory(), BancoFactory()

    resposta = client.post(
        reverse('propostas:criar'),
        {
            **DADOS,
            'beneficio': beneficio.pk,
            'banco': banco.pk,
            'modalidade': ModalidadeFactory().pk,
        },
    )

    proposta = Proposta.objects.get()
    assert resposta.status_code == 302
    assert resposta.url == reverse('propostas:detalhe', args=[proposta.pk])
    assert proposta.operador == operador


def test_banco_inativo_volta_com_erro(client, operador):
    beneficio, banco = BeneficioFactory(), BancoFactory(ativo=False)

    resposta = client.post(
        reverse('propostas:criar'),
        {
            **DADOS,
            'beneficio': beneficio.pk,
            'banco': banco.pk,
            'modalidade': ModalidadeFactory().pk,
        },
    )

    assert resposta.status_code == 200
    assert not Proposta.objects.exists()


def test_lista_filtra_e_responde_fragmento_via_htmx(client, operador):
    banco = BancoFactory(nome='Banco Alvo')
    PropostaFactory(banco=banco)
    PropostaFactory(banco=BancoFactory(nome='Banco Outro'))

    resposta = client.get(
        reverse('propostas:lista'), {'banco': banco.pk}, headers={'HX-Request': 'true'}
    )

    conteudo = resposta.content.decode()
    assert 'Banco Alvo' in conteudo
    assert 'Banco Outro' not in conteudo
    assert '<html' not in conteudo


def test_lista_ignora_filtros_invalidos(client, operador):
    PropostaFactory()

    resposta = client.get(reverse('propostas:lista'), {'banco': 'x', 'status': 'y'})

    assert resposta.status_code == 200


def test_operador_edita_condicoes_e_observacoes(client, operador):
    proposta = PropostaFactory()

    resposta = client.post(
        reverse('propostas:editar', args=[proposta.pk]),
        {
            **DADOS,
            'beneficio': proposta.beneficio_id,
            'banco': proposta.banco_id,
            'modalidade': proposta.modalidade_id,
        },
    )
    client.post(reverse('propostas:observacoes', args=[proposta.pk]), {'observacoes': 'Nota'})

    proposta.refresh_from_db()
    assert resposta.status_code == 302
    assert proposta.prazo == 60
    assert proposta.observacoes == 'Nota'


def test_operador_envia_proposta(client, operador):
    proposta = PropostaFactory()
    MargemFactory(beneficio=proposta.beneficio)

    resposta = client.post(reverse('propostas:enviar', args=[proposta.pk]))

    proposta.refresh_from_db()
    assert resposta.status_code == 302
    assert proposta.status == Proposta.Status.ENVIADA


def test_envio_com_margem_antiga_pede_confirmacao(client, operador):
    proposta = PropostaFactory()
    MargemFactory(
        beneficio=proposta.beneficio,
        data_consulta=datetime.date.today() - datetime.timedelta(days=45),
    )
    url = reverse('propostas:enviar', args=[proposta.pk])

    resposta = client.post(url)
    assert resposta.status_code == 200
    assert Proposta.objects.get().status == Proposta.Status.DIGITADA

    client.post(url, {'confirmar_margem_antiga': '1'})
    assert Proposta.objects.get().status == Proposta.Status.ENVIADA


def test_ficha_do_cliente_mostra_propostas(client, operador):
    proposta = PropostaFactory()

    resposta = client.get(reverse('clientes:detalhe', args=[proposta.cliente.pk]))

    assert reverse('propostas:detalhe', args=[proposta.pk]) in resposta.content.decode()


def test_operador_acompanha_e_cancela(client, operador):
    proposta = PropostaFactory(status=Proposta.Status.ENVIADA)

    client.post(reverse('propostas:avancar', args=[proposta.pk, 'em_analise']))
    client.post(reverse('propostas:cancelar', args=[proposta.pk]), {'motivo': 'Desistiu'})

    proposta.refresh_from_db()
    assert proposta.status == Proposta.Status.CANCELADA
    conteudo = client.get(reverse('propostas:detalhe', args=[proposta.pk])).content.decode()
    assert 'Desistiu' in conteudo
    assert 'Histórico de status' not in conteudo


def test_supervisor_ve_historico_e_cancela_aprovada(client, db):
    supervisor = get_user_model().objects.create_user(username='sup', password='x')
    supervisor.groups.add(Group.objects.get(name='Supervisor'))
    client.force_login(supervisor)
    proposta = PropostaFactory(status=Proposta.Status.APROVADA)

    client.post(reverse('propostas:cancelar', args=[proposta.pk]), {'motivo': 'Desistiu'})

    proposta.refresh_from_db()
    assert proposta.status == Proposta.Status.CANCELADA
    conteudo = client.get(reverse('propostas:detalhe', args=[proposta.pk])).content.decode()
    assert 'Histórico de status' in conteudo


@pytest.mark.parametrize(
    'status_final',
    [Proposta.Status.FORMALIZADA, Proposta.Status.RECUSADA, Proposta.Status.CANCELADA],
)
def test_propostas_finais_nao_exibem_opcoes_de_encerramento(client, operador, status_final):
    proposta = PropostaFactory(status=status_final)

    conteudo = client.get(reverse('propostas:detalhe', args=[proposta.pk])).content.decode()

    assert 'Encerrar' not in conteudo
    assert reverse('propostas:recusar', args=[proposta.pk]) not in conteudo
    assert reverse('propostas:cancelar', args=[proposta.pk]) not in conteudo


def test_proposta_digitada_exibe_apenas_cancelamento_e_rejeita_recusa(client, operador):
    proposta = PropostaFactory(status=Proposta.Status.DIGITADA)

    conteudo = client.get(reverse('propostas:detalhe', args=[proposta.pk])).content.decode()

    assert reverse('propostas:cancelar', args=[proposta.pk]) in conteudo
    assert reverse('propostas:recusar', args=[proposta.pk]) not in conteudo
    assert 'Recusada pelo Banco' not in conteudo

    client.post(reverse('propostas:recusar', args=[proposta.pk]), {'motivo': 'Tentativa'})
    proposta.refresh_from_db()
    assert proposta.status == Proposta.Status.DIGITADA


def test_visibilidade_de_encerramento_de_enviada_ate_aprovada(client, operador):
    enviada = PropostaFactory(status=Proposta.Status.ENVIADA)
    html_enviada = client.get(reverse('propostas:detalhe', args=[enviada.pk])).content.decode()
    assert reverse('propostas:recusar', args=[enviada.pk]) in html_enviada
    assert reverse('propostas:cancelar', args=[enviada.pk]) in html_enviada

    aprovada = PropostaFactory(status=Proposta.Status.APROVADA)
    html_operador = client.get(reverse('propostas:detalhe', args=[aprovada.pk])).content.decode()
    assert reverse('propostas:recusar', args=[aprovada.pk]) in html_operador
    assert reverse('propostas:cancelar', args=[aprovada.pk]) not in html_operador

    supervisor = get_user_model().objects.create_user(username='sup2', password='x')
    supervisor.groups.add(Group.objects.get(name='Supervisor'))
    client.force_login(supervisor)
    html_supervisor = client.get(reverse('propostas:detalhe', args=[aprovada.pk])).content.decode()
    assert reverse('propostas:recusar', args=[aprovada.pk]) in html_supervisor
    assert reverse('propostas:cancelar', args=[aprovada.pk]) in html_supervisor


def test_formularios_de_motivo_iniciam_recolhidos_e_permanecem_abertos_com_erro(client, operador):
    proposta = PropostaFactory(status=Proposta.Status.ENVIADA)

    inicial = client.get(reverse('propostas:detalhe', args=[proposta.pk])).content.decode()
    assert 'id="encerrar-recusar" class="collapse"' in inicial
    assert 'id="encerrar-cancelar" class="collapse"' in inicial
    assert 'data-bs-target="#encerrar-recusar" aria-expanded="false"' in inicial
    assert 'data-bs-target="#encerrar-cancelar" aria-expanded="false"' in inicial

    erro_recusa = client.post(
        reverse('propostas:recusar', args=[proposta.pk]), {'motivo': ''}
    ).content.decode()
    assert 'id="encerrar-recusar" class="collapse show"' in erro_recusa
    assert 'data-bs-target="#encerrar-recusar" aria-expanded="true"' in erro_recusa
    assert 'id="encerrar-cancelar" class="collapse"' in erro_recusa

    erro_cancelamento = client.post(
        reverse('propostas:cancelar', args=[proposta.pk]), {'motivo': '   '}
    ).content.decode()
    assert 'id="encerrar-cancelar" class="collapse show"' in erro_cancelamento
    assert 'data-bs-target="#encerrar-cancelar" aria-expanded="true"' in erro_cancelamento
    assert 'id="encerrar-recusar" class="collapse"' in erro_cancelamento


def test_envio_com_parcela_acima_da_margem_mostra_valores_em_reais(client, operador):
    proposta = PropostaFactory(parcela=Decimal('1400.00'))
    MargemFactory(beneficio=proposta.beneficio, valor=Decimal('1350.00'))

    resposta = client.post(reverse('propostas:enviar', args=[proposta.pk]), follow=True)

    conteudo = resposta.content.decode()
    assert 'R$ 1.400,00' in conteudo
    assert 'R$ 1.350,00' in conteudo


def test_formulario_proposta_nao_renderiza_select_global_de_beneficios(client, operador):
    BeneficioFactory(numero='11111')
    BeneficioFactory(numero='22222')

    resposta = client.get(reverse('propostas:criar'))
    html = resposta.content.decode()

    assert '<select name="beneficio"' not in html
    assert '<input type="hidden" name="beneficio"' in html


def test_abrir_nova_proposta_com_beneficio_valido_exibe_card_de_contexto(client, operador):
    beneficio = BeneficioFactory(numero='1234567890', especie='aposentadoria')
    MargemFactory(
        beneficio=beneficio,
        valor=Decimal('750.50'),
        data_consulta=datetime.date.today(),
    )

    resposta = client.get(reverse('propostas:criar'), {'beneficio': beneficio.pk})
    html = resposta.content.decode()

    assert '1234567890' in html
    assert 'Aposentadoria' in html
    assert beneficio.cliente.nome in html
    assert 'R$ 750,50' in html
    assert 'Trocar Benefício' in html
    assert f'value="{beneficio.pk}"' in html


def test_abrir_nova_proposta_sem_beneficio_exibe_campo_de_busca_htmx(client, operador):
    resposta = client.get(reverse('propostas:criar'))
    html = resposta.content.decode()

    assert 'hx-get=' in html
    assert 'Buscar Benefício por CPF, nome do Cliente ou número do Benefício' in html
    assert 'Trocar Benefício' not in html


def test_abrir_nova_proposta_com_beneficio_inativo_ignora_e_exibe_busca(client, operador):
    inativo = BeneficioFactory(ativo=False)

    resposta = client.get(reverse('propostas:criar'), {'beneficio': inativo.pk})
    html = resposta.content.decode()

    assert 'Buscar Benefício por CPF, nome do Cliente ou número do Benefício' in html
    assert 'Trocar Benefício' not in html


def test_busca_htmx_beneficios_retorna_apenas_ativos_e_permite_selecionar(client, operador):
    b1 = BeneficioFactory(cliente__nome='Carlos Souza', numero='55555')
    BeneficioFactory(ativo=False, numero='55556')
    MargemFactory(beneficio=b1, valor=Decimal('820.00'))

    resposta = client.get(reverse('propostas:buscar_beneficios'), {'q': 'Carlos'})
    html = resposta.content.decode()

    assert 'Carlos Souza' in html
    assert '55555' in html
    assert '55556' not in html
    assert 'R$ 820,00' in html
    assert reverse('propostas:card_beneficio', args=[b1.pk]) in html
    assert 'Selecionar' in html


def test_modo_busca_retorna_formulario_de_busca_e_limpa_beneficio_oob(client, operador):
    resposta = client.get(reverse('propostas:buscar_beneficios'), {'modo': 'busca'})
    html = resposta.content.decode()

    assert 'id="beneficio-selecao"' in html
    assert 'hx-swap-oob="true"' in html
    assert 'value="" id="id_beneficio"' in html


def test_card_beneficio_retorna_card_e_atualiza_beneficio_oob(client, operador):
    b = BeneficioFactory(numero='777888', especie='pensao')
    MargemFactory(beneficio=b, valor=Decimal('450.00'))

    resposta = client.get(reverse('propostas:card_beneficio', args=[b.pk]))
    html = resposta.content.decode()

    assert 'id="beneficio-selecao"' in html
    assert '777888' in html
    assert 'Pensão' in html
    assert 'R$ 450,00' in html
    assert f'value="{b.pk}" id="id_beneficio"' in html
    assert 'hx-swap-oob="true"' in html


def test_edicao_proposta_digitada_preserva_beneficio_inativo_e_permite_trocar(client, operador):
    b1 = BeneficioFactory(numero='111222')
    proposta = PropostaFactory(beneficio=b1, status=Proposta.Status.DIGITADA)
    b1.ativo = False
    b1.save()

    resposta = client.get(reverse('propostas:editar', args=[proposta.pk]))
    html = resposta.content.decode()

    assert '111222' in html
    assert 'Inativo' in html
    assert 'Trocar Benefício' in html

    # Salva mantendo o mesmo benefício (mesmo inativo)
    resp_salvar = client.post(
        reverse('propostas:editar', args=[proposta.pk]),
        {
            **DADOS,
            'beneficio': b1.pk,
            'banco': proposta.banco_id,
            'modalidade': proposta.modalidade_id,
        },
    )
    assert resp_salvar.status_code == 302
    proposta.refresh_from_db()
    assert proposta.beneficio == b1

    # Troca por outro benefício ativo
    b2 = BeneficioFactory(numero='333444', ativo=True)
    resp_troca = client.post(
        reverse('propostas:editar', args=[proposta.pk]),
        {
            **DADOS,
            'beneficio': b2.pk,
            'banco': proposta.banco_id,
            'modalidade': proposta.modalidade_id,
        },
    )
    assert resp_troca.status_code == 302
    proposta.refresh_from_db()
    assert proposta.beneficio == b2


def test_atualizacao_inline_de_margem_a_partir_do_formulario(client, operador):
    beneficio = BeneficioFactory()

    resposta = client.post(
        reverse('propostas:registrar_margem_inline', args=[beneficio.pk]),
        {
            'valor': '650.00',
            'data_consulta': datetime.date.today().isoformat(),
        },
    )

    assert resposta.status_code == 200
    html = resposta.content.decode()
    assert 'R$ 650,00' in html
    assert f'value="{beneficio.pk}" id="id_beneficio"' in html
    assert beneficio.margens.count() == 1


def test_atualizacao_inline_de_margem_com_erro_de_validacao_mantem_formulario_aberto(
    client, operador
):
    beneficio = BeneficioFactory()

    # Valor negativo
    resposta = client.post(
        reverse('propostas:registrar_margem_inline', args=[beneficio.pk]),
        {
            'valor': '-50.00',
            'data_consulta': datetime.date.today().isoformat(),
        },
    )
    assert resposta.status_code == 200
    assert 'A Margem deve ser maior que zero' in resposta.content.decode()
    assert beneficio.margens.count() == 0

    # Data futura
    amanha = datetime.date.today() + datetime.timedelta(days=1)
    resposta_futuro = client.post(
        reverse('propostas:registrar_margem_inline', args=[beneficio.pk]),
        {
            'valor': '500.00',
            'data_consulta': amanha.isoformat(),
        },
    )
    assert resposta_futuro.status_code == 200
    assert 'A data da consulta não pode estar no futuro' in resposta_futuro.content.decode()
    assert beneficio.margens.count() == 0


def test_atualizacao_inline_de_margem_sem_permissao_retorna_403(client, db):
    user_sem_margem = get_user_model().objects.create_user(username='sem_margem', password='x')
    user_sem_margem.groups.add(Group.objects.get(name='Operador'))
    # Remove a permissão de add_margem
    from django.contrib.auth.models import Permission

    perm = Permission.objects.get(codename='add_margem')
    user_sem_margem.user_permissions.remove(perm)
    # E remove do grupo temporariamente para testar
    operador_group = Group.objects.get(name='Operador')
    operador_group.permissions.remove(perm)
    try:
        client.force_login(user_sem_margem)
        beneficio = BeneficioFactory()
        resposta = client.post(
            reverse('propostas:registrar_margem_inline', args=[beneficio.pk]),
            {'valor': '500.00', 'data_consulta': datetime.date.today().isoformat()},
        )
        assert resposta.status_code == 403
    finally:
        operador_group.permissions.add(perm)


def test_detalhe_proposta_digitada_exibe_margem_vigente_e_permite_atualizacao_inline(
    client, operador
):
    beneficio = BeneficioFactory()
    proposta = PropostaFactory(beneficio=beneficio, status=Proposta.Status.DIGITADA)

    # Sem margem
    html_sem = client.get(reverse('propostas:detalhe', args=[proposta.pk])).content.decode()
    assert 'Nenhuma Margem registrada' in html_sem

    # Com margem > 30 dias
    antiga = datetime.date.today() - datetime.timedelta(days=45)
    MargemFactory(beneficio=beneficio, valor=Decimal('400.00'), data_consulta=antiga)
    html_antiga = client.get(reverse('propostas:detalhe', args=[proposta.pk])).content.decode()
    assert 'R$ 400,00' in html_antiga
    assert 'Mais de 30 dias' in html_antiga

    # Atualiza inline via HTMX com origem=detalhe
    hoje = datetime.date.today()
    resp_inline = client.post(
        f"{reverse('propostas:registrar_margem_inline', args=[beneficio.pk])}?origem=detalhe",
        {'valor': '520.00', 'data_consulta': hoje.isoformat()},
    )
    assert resp_inline.status_code == 200
    html_resp = resp_inline.content.decode()
    assert 'id="proposta-margem-detalhe"' in html_resp
    assert 'R$ 520,00' in html_resp
    assert 'Mais de 30 dias' not in html_resp


def test_formulario_exibe_botoes_salvar_digitada_e_salvar_enviar(client, operador):
    beneficio = BeneficioFactory()
    proposta = PropostaFactory(beneficio=beneficio)

    # Criação
    resp_criar = client.get(reverse('propostas:criar'), {'beneficio': beneficio.pk})
    conteudo_criar = resp_criar.content.decode()
    assert 'name="acao" value="salvar_digitada">Salvar como Digitada</button>' in conteudo_criar
    assert 'name="acao" value="salvar_enviar">Salvar e Enviar ao Banco</button>' in conteudo_criar

    # Edição
    resp_editar = client.get(reverse('propostas:editar', args=[proposta.pk]))
    conteudo_editar = resp_editar.content.decode()
    assert 'name="acao" value="salvar_digitada">Salvar como Digitada</button>' in conteudo_editar
    assert 'name="acao" value="salvar_enviar">Salvar e Enviar ao Banco</button>' in conteudo_editar


def test_salvar_como_digitada_permite_sem_margem(client, operador):
    beneficio, banco, modalidade = BeneficioFactory(), BancoFactory(), ModalidadeFactory()

    resposta = client.post(
        reverse('propostas:criar'),
        {
            **DADOS,
            'beneficio': beneficio.pk,
            'banco': banco.pk,
            'modalidade': modalidade.pk,
            'acao': 'salvar_digitada',
        },
    )

    proposta = Proposta.objects.get()
    assert resposta.status_code == 302
    assert proposta.status == Proposta.Status.DIGITADA


def test_salvar_como_digitada_permite_parcela_acima_da_margem(client, operador):
    beneficio, banco, modalidade = BeneficioFactory(), BancoFactory(), ModalidadeFactory()
    MargemFactory(beneficio=beneficio, valor=Decimal('150.00'))

    resposta = client.post(
        reverse('propostas:criar'),
        {
            **DADOS,  # parcela = 200.00
            'beneficio': beneficio.pk,
            'banco': banco.pk,
            'modalidade': modalidade.pk,
            'acao': 'salvar_digitada',
        },
    )

    proposta = Proposta.objects.get()
    assert resposta.status_code == 302
    assert proposta.status == Proposta.Status.DIGITADA


def test_detalhe_proposta_digitada_exibe_alerta_preventivo_sem_margem(client, operador):
    proposta = PropostaFactory(status=Proposta.Status.DIGITADA)

    resposta = client.get(reverse('propostas:detalhe', args=[proposta.pk]))
    conteudo = resposta.content.decode()

    assert 'id="alerta-impedimento-envio"' in conteudo
    assert 'não possui Margem' in conteudo


def test_detalhe_proposta_digitada_exibe_alerta_preventivo_parcela_acima_da_margem(
    client, operador
):
    beneficio = BeneficioFactory()
    MargemFactory(beneficio=beneficio, valor=Decimal('150.00'))
    proposta = PropostaFactory(
        beneficio=beneficio, parcela=Decimal('200.00'), status=Proposta.Status.DIGITADA
    )

    resposta = client.get(reverse('propostas:detalhe', args=[proposta.pk]))
    conteudo = resposta.content.decode()

    assert 'id="alerta-impedimento-envio"' in conteudo
    assert 'R$ 200,00' in conteudo
    assert 'R$ 150,00' in conteudo


def test_detalhe_proposta_digitada_exibe_alerta_preventivo_margem_antiga(client, operador):
    beneficio = BeneficioFactory()
    MargemFactory(
        beneficio=beneficio,
        valor=Decimal('500.00'),
        data_consulta=datetime.date.today() - datetime.timedelta(days=45),
    )
    proposta = PropostaFactory(
        beneficio=beneficio, parcela=Decimal('200.00'), status=Proposta.Status.DIGITADA
    )

    resposta = client.get(reverse('propostas:detalhe', args=[proposta.pk]))
    conteudo = resposta.content.decode()

    assert 'id="alerta-impedimento-envio"' in conteudo
    assert 'mais de 30 dias' in conteudo


def test_detalhe_proposta_digitada_sem_alerta_quando_margem_valida(client, operador):
    beneficio = BeneficioFactory()
    MargemFactory(beneficio=beneficio, valor=Decimal('500.00'))
    proposta = PropostaFactory(
        beneficio=beneficio, parcela=Decimal('200.00'), status=Proposta.Status.DIGITADA
    )

    resposta = client.get(reverse('propostas:detalhe', args=[proposta.pk]))
    conteudo = resposta.content.decode()

    assert 'id="alerta-impedimento-envio"' not in conteudo


def test_salvar_e_enviar_ao_banco_cria_direto_em_status_enviada(client, operador):
    beneficio, banco, modalidade = BeneficioFactory(), BancoFactory(), ModalidadeFactory()
    MargemFactory(beneficio=beneficio, valor=Decimal('500.00'))

    resposta = client.post(
        reverse('propostas:criar'),
        {
            **DADOS,
            'beneficio': beneficio.pk,
            'banco': banco.pk,
            'modalidade': modalidade.pk,
            'acao': 'salvar_enviar',
        },
        follow=True,
    )

    proposta = Proposta.objects.get()
    assert proposta.status == Proposta.Status.ENVIADA
    assert 'Proposta enviada ao Banco.' in resposta.content.decode()


def test_salvar_e_enviar_ao_banco_sem_margem_nao_cria_orfa_e_exibe_erro_no_form(client, operador):
    beneficio, banco, modalidade = BeneficioFactory(), BancoFactory(), ModalidadeFactory()

    resposta = client.post(
        reverse('propostas:criar'),
        {
            **DADOS,
            'beneficio': beneficio.pk,
            'banco': banco.pk,
            'modalidade': modalidade.pk,
            'acao': 'salvar_enviar',
        },
    )

    assert resposta.status_code == 200
    assert Proposta.objects.count() == 0
    assert 'não tem Margem consignável registrada' in resposta.content.decode()


def test_salvar_e_enviar_ao_banco_parcela_acima_da_margem_nao_cria_orfa_e_exibe_erro_no_form(
    client, operador
):
    beneficio, banco, modalidade = BeneficioFactory(), BancoFactory(), ModalidadeFactory()
    MargemFactory(beneficio=beneficio, valor=Decimal('150.00'))

    resposta = client.post(
        reverse('propostas:criar'),
        {
            **DADOS,  # parcela = 200.00
            'beneficio': beneficio.pk,
            'banco': banco.pk,
            'modalidade': modalidade.pk,
            'acao': 'salvar_enviar',
        },
    )

    assert resposta.status_code == 200
    assert Proposta.objects.count() == 0
    conteudo = resposta.content.decode()
    assert 'maior que a Margem vigente' in conteudo
    assert 'R$ 200,00' in conteudo
    assert 'R$ 150,00' in conteudo


def test_salvar_e_enviar_ao_banco_margem_antiga_pede_confirmacao_e_conclui_apos_confirmar(
    client, operador
):
    beneficio, banco, modalidade = BeneficioFactory(), BancoFactory(), ModalidadeFactory()
    MargemFactory(
        beneficio=beneficio,
        valor=Decimal('500.00'),
        data_consulta=datetime.date.today() - datetime.timedelta(days=45),
    )

    # 1. Sem confirmação: não grava proposta e exibe opção de confirmação no form
    dados_post = {
        **DADOS,
        'beneficio': beneficio.pk,
        'banco': banco.pk,
        'modalidade': modalidade.pk,
        'acao': 'salvar_enviar',
    }
    resposta_1 = client.post(reverse('propostas:criar'), dados_post)
    assert resposta_1.status_code == 200
    assert Proposta.objects.count() == 0
    conteudo_1 = resposta_1.content.decode()
    assert 'id="id_confirmar_margem_antiga"' in conteudo_1
    assert 'mais de 30 dias' in conteudo_1

    # 2. Com confirmação: cria direto como ENVIADA
    resposta_2 = client.post(
        reverse('propostas:criar'),
        {**dados_post, 'confirmar_margem_antiga': '1'},
        follow=True,
    )
    proposta = Proposta.objects.get()
    assert proposta.status == Proposta.Status.ENVIADA
    assert 'Proposta enviada ao Banco.' in resposta_2.content.decode()


def test_editar_salvar_e_enviar_ao_banco_atualiza_e_envia(client, operador):
    beneficio = BeneficioFactory()
    MargemFactory(beneficio=beneficio, valor=Decimal('500.00'))
    proposta = PropostaFactory(beneficio=beneficio, status=Proposta.Status.DIGITADA)

    resposta = client.post(
        reverse('propostas:editar', args=[proposta.pk]),
        {
            'beneficio': proposta.beneficio_id,
            'banco': proposta.banco_id,
            'modalidade': proposta.modalidade_id,
            'valor': '15000.00',
            'valor_liberado': '14000.00',
            'prazo': '72',
            'parcela': '450.00',
            'taxa': '1.7500',
            'observacoes': 'Enviando na edição',
            'acao': 'salvar_enviar',
        },
        follow=True,
    )

    proposta.refresh_from_db()
    assert proposta.status == Proposta.Status.ENVIADA
    assert proposta.parcela == Decimal('450.00')
    assert proposta.observacoes == 'Enviando na edição'
    assert 'Proposta enviada ao Banco.' in resposta.content.decode()


def test_editar_salvar_e_enviar_ao_banco_parcela_acima_da_margem_nao_altera_proposta(
    client, operador
):
    beneficio = BeneficioFactory()
    MargemFactory(beneficio=beneficio, valor=Decimal('300.00'))
    proposta = PropostaFactory(
        beneficio=beneficio, parcela=Decimal('200.00'), status=Proposta.Status.DIGITADA
    )

    resposta = client.post(
        reverse('propostas:editar', args=[proposta.pk]),
        {
            'beneficio': proposta.beneficio_id,
            'banco': proposta.banco_id,
            'modalidade': proposta.modalidade_id,
            'valor': '15000.00',
            'valor_liberado': '14000.00',
            'prazo': '72',
            'parcela': '450.00',
            'taxa': '1.7500',
            'observacoes': 'Tentando parcela alta',
            'acao': 'salvar_enviar',
        },
    )

    assert resposta.status_code == 200
    proposta.refresh_from_db()
    assert proposta.status == Proposta.Status.DIGITADA
    assert proposta.parcela == Decimal('200.00')
    assert proposta.observacoes != 'Tentando parcela alta'
    conteudo = resposta.content.decode()
    assert 'maior que a Margem vigente' in conteudo
    assert 'R$ 450,00' in conteudo
    assert 'R$ 300,00' in conteudo


def test_editar_salvar_e_enviar_ao_banco_margem_antiga_fluxo_confirmacao(client, operador):
    beneficio = BeneficioFactory()
    MargemFactory(
        beneficio=beneficio,
        valor=Decimal('500.00'),
        data_consulta=datetime.date.today() - datetime.timedelta(days=45),
    )
    proposta = PropostaFactory(
        beneficio=beneficio, parcela=Decimal('200.00'), status=Proposta.Status.DIGITADA
    )

    dados_post = {
        'beneficio': proposta.beneficio_id,
        'banco': proposta.banco_id,
        'modalidade': proposta.modalidade_id,
        'valor': '15000.00',
        'valor_liberado': '14000.00',
        'prazo': '72',
        'parcela': '300.00',
        'taxa': '1.7500',
        'observacoes': 'Ajuste com margem antiga',
        'acao': 'salvar_enviar',
    }

    # 1. Sem confirmação
    resp_1 = client.post(reverse('propostas:editar', args=[proposta.pk]), dados_post)
    assert resp_1.status_code == 200
    proposta.refresh_from_db()
    assert proposta.status == Proposta.Status.DIGITADA
    assert proposta.parcela == Decimal('200.00')
    assert 'id="id_confirmar_margem_antiga"' in resp_1.content.decode()

    # 2. Com confirmação
    resp_2 = client.post(
        reverse('propostas:editar', args=[proposta.pk]),
        {**dados_post, 'confirmar_margem_antiga': '1'},
        follow=True,
    )
    proposta.refresh_from_db()
    assert proposta.status == Proposta.Status.ENVIADA
    assert proposta.parcela == Decimal('300.00')
    assert 'Proposta enviada ao Banco.' in resp_2.content.decode()




