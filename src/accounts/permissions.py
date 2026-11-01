from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied

MENSAGEM_PERMISSAO_NEGADA = 'Você não tem permissão para acessar esta página.'


class PermissaoNecessariaMixin(PermissionRequiredMixin):
    """Exige a(s) permissão(ões) nativa(s) do Django declarada(s) em `permission_required`.

    Usuário autenticado sem permissão recebe 403 com mensagem em português
    (o login já é exigido globalmente pelo middleware).
    """

    permission_denied_message = MENSAGEM_PERMISSAO_NEGADA

    def handle_no_permission(self):
        raise PermissionDenied(self.get_permission_denied_message())
