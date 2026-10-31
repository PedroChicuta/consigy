from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from accounts.permissions import PermissaoNecessariaMixin
from bancos import selectors as bancos_selectors
from core.exceptions import ErroDeNegocio
from propostas import selectors, services
from propostas.exceptions import MargemAntigaSemConfirmacao
from propostas.forms import ObservacoesForm, PropostaForm
from propostas.models import Proposta

POR_PAGINA = 25


def _pk_ou_vazio(valor):
    return valor if valor and valor.isdigit() else ''


class ListaView(PermissaoNecessariaMixin, View):
    permission_required = 'propostas.view_proposta'

    def get(self, request):
        status = request.GET.get('status', '')
        if status not in Proposta.Status.values:
            status = ''
        banco = _pk_ou_vazio(request.GET.get('banco', ''))
        cliente = request.GET.get('cliente', '').strip()
        propostas = selectors.listar_propostas(status=status, banco=banco, cliente=cliente)
        pagina = Paginator(propostas, POR_PAGINA).get_page(request.GET.get('page'))
        contexto = {
            'pagina': pagina,
            'status': status,
            'banco': banco,
            'cliente': cliente,
            'status_opcoes': Proposta.Status.choices,
            'bancos': bancos_selectors.listar_bancos(),
        }
        template = 'propostas/lista.html'
        if request.headers.get('HX-Request'):
            template = 'propostas/partials/_tabela.html'
        return render(request, template, contexto)


class CriarView(PermissaoNecessariaMixin, View):
    permission_required = 'propostas.add_proposta'

    def get(self, request):
        inicial = {}
        beneficio = _pk_ou_vazio(request.GET.get('beneficio', ''))
        if beneficio:
            inicial['beneficio'] = beneficio
        return render(request, 'propostas/form.html', {'form': PropostaForm(initial=inicial)})

    def post(self, request):
        form = PropostaForm(request.POST)
        if form.is_valid():
            try:
                proposta = services.criar_proposta(usuario=request.user, **form.cleaned_data)
            except ErroDeNegocio as erro:
                form.add_error(None, str(erro))
            else:
                messages.success(request, 'Proposta registrada.')
                return redirect('propostas:detalhe', pk=proposta.pk)
        return render(request, 'propostas/form.html', {'form': form})


def _buscar(pk):
    return get_object_or_404(
        Proposta.objects.select_related('beneficio__cliente', 'banco', 'operador'), pk=pk
    )


class DetalheView(PermissaoNecessariaMixin, View):
    permission_required = 'propostas.view_proposta'

    def get(self, request, pk):
        proposta = _buscar(pk)
        return render(request, 'propostas/detalhe.html', _contexto_detalhe(proposta))


def _contexto_detalhe(proposta, **extra):
    return {
        'proposta': proposta,
        'form_observacoes': ObservacoesForm(initial={'observacoes': proposta.observacoes}),
        **extra,
    }


class EnviarView(PermissaoNecessariaMixin, View):
    permission_required = 'propostas.change_proposta'
    http_method_names = ['post']

    def post(self, request, pk):
        proposta = _buscar(pk)
        confirmar = request.POST.get('confirmar_margem_antiga') == '1'
        try:
            services.enviar_proposta(
                usuario=request.user, proposta=proposta, confirmar_margem_antiga=confirmar
            )
        except MargemAntigaSemConfirmacao as erro:
            messages.warning(request, str(erro))
            contexto = _contexto_detalhe(proposta, pedir_confirmacao=True)
            return render(request, 'propostas/detalhe.html', contexto)
        except ErroDeNegocio as erro:
            messages.error(request, str(erro))
        else:
            messages.success(request, 'Proposta enviada ao Banco.')
        return redirect('propostas:detalhe', pk=proposta.pk)


class EditarView(PermissaoNecessariaMixin, View):
    permission_required = 'propostas.change_proposta'

    def _dados_iniciais(self, proposta):
        return {
            'beneficio': proposta.beneficio_id,
            'banco': proposta.banco_id,
            'valor': proposta.valor,
            'prazo': proposta.prazo,
            'parcela': proposta.parcela,
            'taxa': proposta.taxa,
            'observacoes': proposta.observacoes,
        }

    def get(self, request, pk):
        proposta = _buscar(pk)
        if proposta.status != Proposta.Status.DIGITADA:
            messages.error(request, 'Só é possível alterar as condições de uma Proposta Digitada.')
            return redirect('propostas:detalhe', pk=proposta.pk)
        form = PropostaForm(initial=self._dados_iniciais(proposta), proposta=proposta)
        return render(request, 'propostas/form.html', {'form': form, 'proposta': proposta})

    def post(self, request, pk):
        proposta = _buscar(pk)
        form = PropostaForm(request.POST, proposta=proposta)
        if form.is_valid():
            try:
                services.editar_proposta(
                    usuario=request.user, proposta=proposta, **form.cleaned_data
                )
            except ErroDeNegocio as erro:
                form.add_error(None, str(erro))
            else:
                messages.success(request, 'Proposta atualizada.')
                return redirect('propostas:detalhe', pk=proposta.pk)
        return render(request, 'propostas/form.html', {'form': form, 'proposta': proposta})


class EditarObservacoesView(PermissaoNecessariaMixin, View):
    permission_required = 'propostas.change_proposta'
    http_method_names = ['post']

    def post(self, request, pk):
        proposta = _buscar(pk)
        form = ObservacoesForm(request.POST)
        if form.is_valid():
            services.editar_observacoes(
                usuario=request.user, proposta=proposta, **form.cleaned_data
            )
            messages.success(request, 'Observações atualizadas.')
        return redirect('propostas:detalhe', pk=proposta.pk)
