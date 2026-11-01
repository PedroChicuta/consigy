import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.http import HttpResponse
from django.urls import include, path
from django.views import View

from accounts.permissions import PermissaoNecessariaMixin

SENHA = 'senha-forte-123'


class ViewProtegida(PermissaoNecessariaMixin, View):
    permission_required = 'accounts.view_user'

    def get(self, request):
        return HttpResponse('conteudo protegido')


urlpatterns = [
    path('protegida/', ViewProtegida.as_view(), name='protegida'),
    path('', include('accounts.urls')),
    path('', include('inicio.urls')),
]


@pytest.fixture
def usuario(db):
    return get_user_model().objects.create_user(username='joao', password=SENHA)


@pytest.mark.parametrize('nome', ['Operador', 'Supervisor'])
def test_grupos_criados_por_migration(db, nome):
    assert Group.objects.filter(name=nome).exists()


def test_admin_cria_usuario_e_atribui_grupo(client, db):
    admin_user = get_user_model().objects.create_superuser(username='root', password=SENHA)
    client.force_login(admin_user)

    resposta = client.post(
        '/admin/accounts/user/add/',
        {'username': 'novo', 'password1': SENHA + 'x', 'password2': SENHA + 'x'},
    )
    assert resposta.status_code == 302
    novo = get_user_model().objects.get(username='novo')
    novo.groups.add(Group.objects.get(name='Operador'))

    assert novo.groups.filter(name='Operador').exists()
    assert client.get(f'/admin/accounts/user/{novo.pk}/change/').status_code == 200


@pytest.mark.urls('accounts.tests.test_permissoes')
def test_sem_permissao_e_barrado_com_mensagem_em_portugues(client, usuario):
    client.force_login(usuario)

    resposta = client.get('/protegida/')

    assert resposta.status_code == 403
    conteudo = resposta.content.decode()
    assert 'Você não tem permissão para acessar esta página.' in conteudo
    assert 'conteudo protegido' not in conteudo


@pytest.mark.urls('accounts.tests.test_permissoes')
def test_com_permissao_passa(client, usuario):
    usuario.user_permissions.add(Permission.objects.get(codename='view_user'))
    client.force_login(usuario)

    resposta = client.get('/protegida/')

    assert resposta.status_code == 200
    assert resposta.content.decode() == 'conteudo protegido'


@pytest.mark.urls('accounts.tests.test_permissoes')
def test_permissao_via_grupo_passa(client, usuario):
    grupo = Group.objects.get(name='Supervisor')
    grupo.permissions.add(Permission.objects.get(codename='view_user'))
    usuario.groups.add(grupo)
    client.force_login(usuario)

    assert client.get('/protegida/').status_code == 200
