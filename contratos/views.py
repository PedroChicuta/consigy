from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from accounts.permissions import PermissaoNecessariaMixin
from contratos import selectors, services
from contratos.forms import MotivoForm
from contratos.models import Contrato
from core.exceptions import ErroDeNegocio

POR_PAGINA = 25


class ListaView(PermissaoNecessariaMixin, View):
    permission_required = 'contratos.view_contrato'

    def get(self, request):
        status = request.GET.get('status', '')
        if status not in Contrato.Status.values:
            status = ''
        cliente = request.GET.get('cliente', '').strip()
        contratos = selectors.listar_contratos(status=status, cliente=cliente)
        pagina = Paginator(contratos, POR_PAGINA).get_page(request.GET.get('page'))
        contexto = {
            'pagina': pagina,
            'status': status,
            'cliente': cliente,
            'status_opcoes': Contrato.Status.choices,
        }
        template = 'contratos/lista.html'
        if request.headers.get('HX-Request'):
            template = 'contratos/partials/_tabela.html'
        return render(request, template, contexto)


def _buscar(pk):
    return get_object_or_404(
        Contrato.objects.select_related('proposta__beneficio__cliente', 'proposta__banco'), pk=pk
    )


class DetalheView(PermissaoNecessariaMixin, View):
    permission_required = 'contratos.view_contrato'

    def get(self, request, pk):
        contrato = _buscar(pk)
        historico = None
        if request.user.has_perm('contratos.view_historicalcontrato'):
            historico = selectors.historico_do_contrato(contrato=contrato)
        return render(
            request, 'contratos/detalhe.html', {'contrato': contrato, 'historico': historico}
        )


class AvancarView(PermissaoNecessariaMixin, View):
    permission_required = 'contratos.change_contrato'
    http_method_names = ['post']

    def post(self, request, pk, status):
        contrato = _buscar(pk)
        try:
            services.avancar_contrato(usuario=request.user, contrato=contrato, status=status)
        except ErroDeNegocio as erro:
            messages.error(request, str(erro))
        else:
            messages.success(request, f'Contrato {contrato.get_status_display().lower()}.')
        return redirect('contratos:detalhe', pk=contrato.pk)


class CancelarView(PermissaoNecessariaMixin, View):
    permission_required = 'contratos.change_contrato'
    http_method_names = ['post']

    def post(self, request, pk):
        contrato = _buscar(pk)
        form = MotivoForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Informe o motivo.')
        else:
            try:
                services.cancelar_contrato(
                    usuario=request.user, contrato=contrato, **form.cleaned_data
                )
            except ErroDeNegocio as erro:
                messages.error(request, str(erro))
            else:
                messages.success(request, 'Contrato cancelado.')
        return redirect('contratos:detalhe', pk=contrato.pk)
