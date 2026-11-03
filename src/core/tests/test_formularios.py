import pytest
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.template import Context, Template
from django.urls import reverse


class _Form(forms.Form):
    nome = forms.CharField(label='Nome')
    especie = forms.ChoiceField(label='Espécie', choices=[('41', 'Aposentadoria')])
    email = forms.EmailField(label='E-mail', required=False, help_text='Para contato.')
    observacoes = forms.CharField(required=False, widget=forms.Textarea)
    aceito = forms.BooleanField(label='Aceito', required=False)
    marcado = forms.CharField(widget=forms.TextInput(attrs={'class': 'font-monospace'}))
    oculto = forms.CharField(required=False, widget=forms.HiddenInput)


def test_cada_widget_recebe_a_classe_bootstrap():
    form = _Form()

    assert 'class="form-control"' in str(form['nome'])
    assert 'class="form-select"' in str(form['especie'])
    assert 'class="form-check-input"' in str(form['aceito'])
    assert 'class="font-monospace form-control"' in str(form['marcado'])
    assert 'class=' not in str(form['oculto'])


def test_campo_com_erro_fica_invalido_e_mostra_a_mensagem_ligada_ao_input():
    form = _Form(data={'nome': ''})
    form.is_valid()

    grupo = str(form['nome'].as_field_group())

    assert 'form-control is-invalid' in grupo
    assert 'aria-describedby="id_nome_error"' in grupo
    assert 'class="invalid-feedback d-block" id="id_nome_error"' in grupo
    assert 'Este campo é obrigatório.' in grupo


def test_campo_opcional_e_sinalizado_e_obrigatorio_nao():
    form = _Form()

    assert '(opcional)' in str(form['email'].as_field_group())
    assert '(opcional)' not in str(form['nome'].as_field_group())


def test_texto_de_ajuda_fica_ligado_ao_campo():
    grupo = str(_Form()['email'].as_field_group())

    assert 'class="form-text" id="id_email_helptext"' in grupo
    assert 'aria-describedby="id_email_helptext"' in grupo


def test_form_usa_grade_com_textarea_e_checkbox_em_largura_total():
    html = str(_Form())

    assert 'class="row g-3"' in html
    assert html.count('class="col-12 col-md-6"') == 4
    assert html.count('class="col-12"') == 2


def test_erros_gerais_aparecem_em_alerta():
    form = _Form(data={'nome': 'x', 'especie': '41', 'marcado': 'y'})
    form.is_valid()
    form.add_error(None, 'Benefício inativo.')

    html = str(form)

    assert 'class="alert alert-danger"' in html
    assert 'Benefício inativo.' in html


@pytest.fixture
def client_operador(client, db):
    user = get_user_model().objects.create_user(username='maria', password='x')
    for app, codigo in (('clientes', 'add_cliente'), ('bancos', 'add_banco')):
        user.user_permissions.add(
            Permission.objects.get(content_type__app_label=app, codename=codigo)
        )
    client.force_login(user)
    return client


@pytest.mark.parametrize('rota', ['clientes:criar', 'bancos:criar'])
def test_paginas_de_formulario_seguem_o_padrao(client_operador, rota):
    html = client_operador.get(reverse(rota)).content.decode()

    assert 'class="card shadow-sm"' in html
    assert 'class="card-footer formulario-acoes"' in html
    assert 'class="form-control"' in html
    assert html.index('>Cancelar</a>') < html.index('>Salvar</button>')


def test_cancelar_usa_next_seguro_quando_informado(client_operador):
    resposta = client_operador.get(reverse('clientes:criar'), {'next': '/clientes/42/'})
    html = resposta.content.decode()

    assert 'href="/clientes/42/">Cancelar</a>' in html
    assert 'name="next" value="/clientes/42/"' in html

    html_pos_erro = client_operador.post(
        reverse('clientes:criar'), {'nome': '', 'next': '/clientes/42/'}
    ).content.decode()
    assert 'href="/clientes/42/">Cancelar</a>' in html_pos_erro


@pytest.mark.parametrize(
    'next_invalido',
    [
        'https://malicioso.exemplo/roubo',
        '//malicioso.exemplo/roubo',
        'javascript:alert(1)',
        'caminho-sem-barra',
        '   ',
    ],
)
def test_cancelar_ignora_next_invalido_ou_externo(client_operador, next_invalido):
    html = client_operador.get(reverse('clientes:criar'), {'next': next_invalido}).content.decode()

    assert f'href="{reverse("clientes:lista")}">Cancelar</a>' in html
    assert 'malicioso' not in html


def test_pagina_de_formulario_suporta_botoes_secundarios_de_submissao():
    tpl = Template(
        "{% extends 'formularios/pagina.html' %}"
        "{% block titulo_formulario %}Novo Cliente{% endblock %}"
        "{% block url_cancelar %}/clientes/{% endblock %}"
        "{% block acoes_extras %}"
        '<button class="btn btn-outline-primary" type="submit" name="acao" value="beneficio">'
        'Salvar e adicionar Benefício</button>'
        "{% endblock %}"
    )
    html = tpl.render(
        Context(
            {
                'form': _Form(),
                'acoes_extras': [
                    {'rotulo': 'Ignorado se bloco sobrescrito', 'valor': 'x'},
                ],
            }
        )
    )
    rodape = html.split('formulario-acoes')[1].split('</div>')[0]

    assert 'href="/clientes/">Cancelar</a>' in rodape
    assert 'name="acao" value="beneficio">Salvar e adicionar Benefício</button>' in rodape
    assert '>Salvar</button>' in rodape
    pos_cancelar = rodape.index('Cancelar')
    pos_secundario = rodape.index('Salvar e adicionar Benefício')
    assert pos_cancelar < pos_secundario < rodape.index('>Salvar</button>')


def test_pagina_de_formulario_renderiza_acoes_extras_do_contexto():
    tpl = Template(
        "{% extends 'formularios/pagina.html' %}"
        "{% block titulo_formulario %}Novo Benefício{% endblock %}"
        "{% block url_cancelar %}/clientes/1/{% endblock %}"
    )
    html = tpl.render(
        Context(
            {
                'form': _Form(),
                'acoes_extras': [
                    {'rotulo': 'Salvar e criar Proposta', 'valor': 'criar_proposta'},
                ],
            }
        )
    )
    rodape = html.split('formulario-acoes')[1].split('</div>')[0]

    assert 'name="acao" value="criar_proposta">Salvar e criar Proposta</button>' in rodape
    assert '>Salvar</button>' in rodape


def test_login_segue_o_padrao(client, db):
    html = client.get(reverse('accounts:login')).content.decode()

    assert 'class="card shadow-sm"' in html
    assert 'name="username"' in html
    assert 'form-control' in html

