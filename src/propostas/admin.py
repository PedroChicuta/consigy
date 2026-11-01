from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from propostas.models import Modalidade


@admin.register(Modalidade)
class ModalidadeAdmin(SimpleHistoryAdmin):
    # O SimpleHistoryAdmin grava o usuário que editou no histórico.
    list_display = ['nome', 'ativo', 'envolve_portabilidade']
    list_filter = ['ativo', 'envolve_portabilidade']
    search_fields = ['nome']
