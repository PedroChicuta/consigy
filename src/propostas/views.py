from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from accounts.permissions import PermissaoNecessariaMixin
from bancos import selectors as bancos_selectors
from contratos import selectors as contratos_selectors
from core.exceptions import ErroDeNegocio
from propostas import selectors, services
from propostas.exceptions import MargemAntigaSemConfirmacao
from propostas.forms import MotivoForm, ObservacoesForm, PropostaForm
from propostas.models import Modalidade, Proposta

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
        modalidade = _pk_ou_vazio(request.GET.get('modalidade', ''))
        propostas = selectors.listar_propostas(
            status=status, banco=banco, cliente=cliente, modalidade=modalidade
        )
        pagina = Paginator(propostas, POR_PAGINA).get_page(request.GET.get('page'))
        contexto = {
            'pagina': pagina,
            'status': status,
            'banco': banco,
            'modalidade': modalidade,
            'modalidades': Modalidade.objects.all(),
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
        Proposta.objects.select_related('beneficio__cliente', 'banco', 'modalidade', 'operador'),
        pk=pk,
    )


class DetalheView(PermissaoNecessariaMixin, View):
    permission_required = 'propostas.view_proposta'

    def get(self, request, pk):
        proposta = _buscar(pk)
        historico = None
        if request.user.has_perm('propostas.view_historicalproposta'):
            historico = selectors.historico_da_proposta(proposta=proposta)
        contratos = None
        if request.user.has_perm('contratos.view_contrato'):
            contratos = contratos_selectors.contratos_da_proposta(proposta=proposta)
        return render(
            request,
            'propostas/detalhe.html',
            _contexto_detalhe(proposta, historico=historico, contratos=contratos),
        )


def _contexto_detalhe(proposta, **extra):
    return {
        'proposta': proposta,
        'historico': None,
        'form_observacoes': ObservacoesForm(initial={'observacoes': proposta.observacoes}),
        'form_recusar': MotivoForm(auto_id='recusar_%s'),
        'form_cancelar': MotivoForm(auto_id='cancelar_%s'),
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
            'modalidade': proposta.modalidade_id,
            'valor': proposta.valor,
            'valor_liberado': proposta.valor_liberado,
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


class AvancarView(PermissaoNecessariaMixin, View):
    permission_required = 'propostas.change_proposta'
    http_method_names = ['post']

    def post(self, request, pk, status):
        proposta = _buscar(pk)
        try:
            services.avancar_proposta(usuario=request.user, proposta=proposta, status=status)
        except ErroDeNegocio as erro:
            messages.error(request, str(erro))
        else:
            messages.success(request, f'Proposta {proposta.get_status_display().lower()}.')
        return redirect('propostas:detalhe', pk=proposta.pk)


class FormalizarView(PermissaoNecessariaMixin, View):
    permission_required = 'propostas.change_proposta'
    http_method_names = ['post']

    def post(self, request, pk):
        proposta = _buscar(pk)
        try:
            services.formalizar_proposta(usuario=request.user, proposta=proposta)
        except ErroDeNegocio as erro:
            messages.error(request, str(erro))
        else:
            messages.success(request, 'Proposta formalizada e Contrato criado.')
        return redirect('propostas:detalhe', pk=proposta.pk)


class _EncerrarView(PermissaoNecessariaMixin, View):
    permission_required = 'propostas.change_proposta'
    http_method_names = ['post']
    mensagem = ''

    def encerrar(self, **kwargs):
        raise NotImplementedError

    def post(self, request, pk):
        proposta = _buscar(pk)
        form = MotivoForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Informe o motivo.')
        else:
            try:
                self.encerrar(usuario=request.user, proposta=proposta, **form.cleaned_data)
            except ErroDeNegocio as erro:
                messages.error(request, str(erro))
            else:
                messages.success(request, self.mensagem)
        return redirect('propostas:detalhe', pk=proposta.pk)


class RecusarView(_EncerrarView):
    mensagem = 'Proposta recusada.'

    def encerrar(self, **kwargs):
        services.recusar_proposta(**kwargs)


class CancelarView(_EncerrarView):
    mensagem = 'Proposta cancelada.'

    def encerrar(self, **kwargs):
        services.cancelar_proposta(**kwargs)
