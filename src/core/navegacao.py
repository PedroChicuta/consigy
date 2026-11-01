from dataclasses import dataclass

from django.urls import reverse
from django.utils.text import slugify

# Grupos e áreas na ordem do fluxo do Operador (ADR 0009): (nome, app, permissão).
# Benefícios não tem item próprio: sempre se acessa pelo detalhe do Cliente.
_GRUPOS = (
    (
        'Cadastros',
        (
            ('Clientes', 'clientes', 'clientes.view_cliente'),
            ('Bancos', 'bancos', 'bancos.view_banco'),
        ),
    ),
    (
        'Processos',
        (
            ('Propostas', 'propostas', 'propostas.view_proposta'),
            ('Contratos', 'contratos', 'contratos.view_contrato'),
        ),
    ),
)


@dataclass(frozen=True)
class ItemMenu:
    nome: str
    url: str
    ativo: bool


@dataclass(frozen=True)
class GrupoMenu:
    nome: str
    itens: list[ItemMenu]

    @property
    def slug(self):
        return slugify(self.nome)


def _iniciais(nome):
    partes = nome.split()
    if len(partes) > 1:
        return (partes[0][0] + partes[-1][0]).upper()
    return nome[:2].upper()


def navegacao(request):
    """Disponibiliza aos templates `grupos_menu` (filtrados por permissão) e os dados do
    Operador exibidos na barra superior (`nome_operador`, `iniciais_operador`)."""
    user = request.user
    if not user.is_authenticated:
        return {}
    namespace = request.resolver_match.namespace if request.resolver_match else ''
    grupos = []
    for nome_grupo, areas in _GRUPOS:
        itens = [
            ItemMenu(nome, reverse(f'{app}:lista'), namespace == app)
            for nome, app, permissao in areas
            if user.has_perm(permissao)
        ]
        if itens:
            grupos.append(GrupoMenu(nome_grupo, itens))
    nome = user.get_full_name() or user.get_username()
    return {
        'grupos_menu': grupos,
        'nome_operador': nome,
        'iniciais_operador': _iniciais(nome),
    }
