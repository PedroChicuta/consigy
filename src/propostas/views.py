from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from accounts.permissions import PermissaoNecessariaMixin
from bancos import selectors as bancos_selectors
from beneficios import selectors as beneficios_selectors
from beneficios import services as beneficios_services
from beneficios.forms import MargemForm
from beneficios.models import Beneficio, Margem
from contratos import selectors as contratos_selectors
from core.exceptions import ErroDeNegocio
from propostas import selectors, services
from propostas.exceptions import MargemAntigaSemConfirmacao
from propostas.forms import ModalidadeForm, MotivoForm, ObservacoesForm, PropostaForm
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
            'modalidades': selectors.listar_modalidades(),
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
        beneficio_pk = _pk_ou_vazio(request.GET.get('beneficio', ''))
        beneficio = None
        if beneficio_pk:
            beneficio = (
                Beneficio.objects.select_related('cliente')
                .filter(pk=beneficio_pk, ativo=True, cliente__ativo=True)
                .first()
            )
        inicial = {}
        if beneficio:
            inicial['beneficio'] = beneficio.pk
        return render(
            request,
            'propostas/form.html',
            {
                'form': PropostaForm(initial=inicial),
                'beneficio': beneficio,
            },
        )

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
        beneficio_pk = _pk_ou_vazio(request.POST.get('beneficio', ''))
        beneficio = None
        if beneficio_pk:
            beneficio = Beneficio.objects.select_related('cliente').filter(pk=beneficio_pk).first()
        return render(request, 'propostas/form.html', {'form': form, 'beneficio': beneficio})


class BuscarBeneficiosView(PermissaoNecessariaMixin, View):
    def has_permission(self):
        user = self.request.user
        return user.has_perm('propostas.add_proposta') or user.has_perm(
            'propostas.change_proposta'
        )

    def get(self, request):
        if request.GET.get('modo') == 'busca':
            return render(request, 'propostas/partials/_busca_beneficios.html')
        busca = request.GET.get('q', '').strip()
        beneficios = beneficios_selectors.buscar_beneficios_ativos(busca=busca)
        return render(
            request,
            'propostas/partials/_resultado_busca_beneficios.html',
            {'beneficios': beneficios, 'busca': busca},
        )


class CardBeneficioView(PermissaoNecessariaMixin, View):
    def has_permission(self):
        user = self.request.user
        return user.has_perm('propostas.add_proposta') or user.has_perm(
            'propostas.change_proposta'
        )

    def get(self, request, pk):
        beneficio = get_object_or_404(
            Beneficio.objects.select_related('cliente').prefetch_related(
                Prefetch('margens', queryset=Margem.objects.order_by('-data_consulta', '-pk'))
            ),
            pk=pk,
        )
        return render(
            request,
            'propostas/partials/_card_beneficio.html',
            {'beneficio': beneficio},
        )


class RegistrarMargemInlineView(PermissaoNecessariaMixin, View):
    permission_required = 'beneficios.add_margem'
    http_method_names = ['post']

    def post(self, request, pk):
        beneficio = get_object_or_404(
            Beneficio.objects.select_related('cliente').prefetch_related(
                Prefetch('margens', queryset=Margem.objects.order_by('-data_consulta', '-pk'))
            ),
            pk=pk,
        )
        origem = request.GET.get('origem') or request.POST.get('origem')
        template = (
            'propostas/partials/_margem_detalhe.html'
            if origem == 'detalhe'
            else 'propostas/partials/_card_beneficio.html'
        )

        form = MargemForm(request.POST)
        erro_margem = None
        if form.is_valid():
            try:
                beneficios_services.registrar_margem(
                    usuario=request.user,
                    beneficio=beneficio,
                    **form.cleaned_data,
                )
            except ErroDeNegocio as erro:
                erro_margem = str(erro)
            else:
                beneficio.refresh_from_db()
        else:
            for erros in form.errors.values():
                if erros:
                    erro_margem = erros[0]
                    break

        return render(
            request,
            template,
            {
                'beneficio': beneficio,
                'erro_margem': erro_margem,
            },
        )



def _buscar(pk):
    return get_object_or_404(
        Proposta.objects.select_related(
            'beneficio__cliente', 'banco', 'modalidade', 'operador'
        ).prefetch_related(
            Prefetch(
                'beneficio__margens',
                queryset=Margem.objects.order_by('-data_consulta', '-pk'),
            )
        ),
        pk=pk,
    )



class DetalheView(PermissaoNecessariaMixin, View):
    permission_required = 'propostas.view_proposta'

    def get(self, request, pk):
        proposta = _buscar(pk)
        return render(
            request,
            'propostas/detalhe.html',
            _contexto_detalhe(proposta, usuario=request.user),
        )


def _contexto_detalhe(proposta, *, usuario=None, **extra):
    historico = None
    contratos = None
    if usuario is not None:
        if usuario.has_perm('propostas.view_historicalproposta'):
            historico = selectors.historico_da_proposta(proposta=proposta)
        if usuario.has_perm('contratos.view_contrato'):
            contratos = contratos_selectors.contratos_da_proposta(proposta=proposta)
    return {
        'proposta': proposta,
        'historico': historico,
        'contratos': contratos,
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
            contexto = _contexto_detalhe(proposta, usuario=request.user, pedir_confirmacao=True)
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
        return render(
            request,
            'propostas/form.html',
            {'form': form, 'proposta': proposta, 'beneficio': proposta.beneficio},
        )

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
        beneficio_pk = _pk_ou_vazio(request.POST.get('beneficio', '')) or proposta.beneficio_id
        beneficio = Beneficio.objects.select_related('cliente').filter(pk=beneficio_pk).first()
        return render(
            request,
            'propostas/form.html',
            {'form': form, 'proposta': proposta, 'beneficio': beneficio},
        )


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
            contrato = services.formalizar_proposta(usuario=request.user, proposta=proposta)
        except ErroDeNegocio as erro:
            messages.error(request, str(erro))
            return redirect('propostas:detalhe', pk=proposta.pk)
        messages.success(
            request,
            f'Proposta #{proposta.pk} formalizada. Este é o Contrato #{contrato.pk} gerado.',
        )
        return redirect('contratos:detalhe', pk=contrato.pk)


class _EncerrarView(PermissaoNecessariaMixin, View):
    permission_required = 'propostas.change_proposta'
    http_method_names = ['post']
    mensagem = ''
    auto_id = '%s'
    chave_form = ''

    def encerrar(self, **kwargs):
        raise NotImplementedError

    def post(self, request, pk):
        proposta = _buscar(pk)
        form = MotivoForm(request.POST, auto_id=self.auto_id)
        if not form.is_valid():
            messages.error(request, 'Informe o motivo.')
            contexto = _contexto_detalhe(
                proposta, usuario=request.user, **{self.chave_form: form}
            )
            return render(request, 'propostas/detalhe.html', contexto)
        try:
            self.encerrar(usuario=request.user, proposta=proposta, **form.cleaned_data)
        except ErroDeNegocio as erro:
            messages.error(request, str(erro))
        else:
            messages.success(request, self.mensagem)
        return redirect('propostas:detalhe', pk=proposta.pk)


class RecusarView(_EncerrarView):
    mensagem = 'Proposta recusada.'
    auto_id = 'recusar_%s'
    chave_form = 'form_recusar'

    def encerrar(self, **kwargs):
        services.recusar_proposta(**kwargs)


class CancelarView(_EncerrarView):
    mensagem = 'Proposta cancelada.'
    auto_id = 'cancelar_%s'
    chave_form = 'form_cancelar'

    def encerrar(self, **kwargs):
        services.cancelar_proposta(**kwargs)


class ModalidadeListaView(PermissaoNecessariaMixin, View):
    permission_required = 'propostas.view_modalidade'

    def get(self, request):
        return render(
            request,
            'propostas/modalidades/lista.html',
            {'modalidades': selectors.listar_modalidades()},
        )


class ModalidadeCriarView(PermissaoNecessariaMixin, View):
    permission_required = 'propostas.add_modalidade'

    def get(self, request):
        return render(request, 'propostas/modalidades/form.html', {'form': ModalidadeForm()})

    def post(self, request):
        form = ModalidadeForm(request.POST)
        if form.is_valid():
            try:
                services.criar_modalidade(usuario=request.user, **form.cleaned_data)
            except ErroDeNegocio as erro:
                form.add_error(None, str(erro))
            else:
                messages.success(request, 'Modalidade cadastrada.')
                return redirect('modalidades:lista')
        return render(request, 'propostas/modalidades/form.html', {'form': form})


class ModalidadeEditarView(PermissaoNecessariaMixin, View):
    permission_required = 'propostas.change_modalidade'

    def get(self, request, pk):
        modalidade = get_object_or_404(Modalidade, pk=pk)
        form = ModalidadeForm(
            initial={
                'nome': modalidade.nome,
                'envolve_portabilidade': modalidade.envolve_portabilidade,
            }
        )
        return render(
            request,
            'propostas/modalidades/form.html',
            {'form': form, 'modalidade': modalidade},
        )

    def post(self, request, pk):
        modalidade = get_object_or_404(Modalidade, pk=pk)
        form = ModalidadeForm(request.POST)
        if form.is_valid():
            try:
                services.editar_modalidade(
                    usuario=request.user, modalidade=modalidade, **form.cleaned_data
                )
            except ErroDeNegocio as erro:
                form.add_error(None, str(erro))
            else:
                messages.success(request, 'Modalidade atualizada.')
                return redirect('modalidades:lista')
        return render(
            request,
            'propostas/modalidades/form.html',
            {'form': form, 'modalidade': modalidade},
        )


class _MudarSituacaoModalidadeView(PermissaoNecessariaMixin, View):
    permission_required = 'propostas.change_modalidade'
    http_method_names = ['post']
    mensagem = ''

    def executar(self, *, usuario, modalidade):
        raise NotImplementedError

    def post(self, request, pk):
        modalidade = get_object_or_404(Modalidade, pk=pk)
        try:
            self.executar(usuario=request.user, modalidade=modalidade)
        except ErroDeNegocio as erro:
            messages.error(request, str(erro))
        else:
            messages.success(request, self.mensagem)
        return redirect('modalidades:lista')


class ModalidadeInativarView(_MudarSituacaoModalidadeView):
    mensagem = 'Modalidade inativada.'

    def executar(self, *, usuario, modalidade):
        services.inativar_modalidade(usuario=usuario, modalidade=modalidade)


class ModalidadeReativarView(_MudarSituacaoModalidadeView):
    mensagem = 'Modalidade reativada.'

    def executar(self, *, usuario, modalidade):
        services.reativar_modalidade(usuario=usuario, modalidade=modalidade)
