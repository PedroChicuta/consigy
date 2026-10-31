from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from accounts.permissions import PermissaoNecessariaMixin
from beneficios import selectors as beneficios_selectors
from clientes import selectors, services
from clientes.exceptions import CpfDuplicado
from clientes.forms import ClienteForm, NovoClienteForm
from clientes.models import Cliente
from core.exceptions import ErroDeNegocio

POR_PAGINA = 25


class ListaView(PermissaoNecessariaMixin, View):
    permission_required = 'clientes.view_cliente'

    def get(self, request):
        busca = request.GET.get('q', '').strip()
        paginas = Paginator(selectors.listar_clientes(busca=busca), POR_PAGINA)
        pagina = paginas.get_page(request.GET.get('page'))
        template = 'clientes/lista.html'
        if request.headers.get('HX-Request'):
            template = 'clientes/partials/_tabela.html'
        return render(request, template, {'pagina': pagina, 'busca': busca})


class CriarView(PermissaoNecessariaMixin, View):
    permission_required = 'clientes.add_cliente'

    def get(self, request):
        return render(request, 'clientes/form.html', {'form': NovoClienteForm()})

    def post(self, request):
        form = NovoClienteForm(request.POST)
        if form.is_valid():
            try:
                cliente = services.criar_cliente(usuario=request.user, **form.cleaned_data)
            except CpfDuplicado as erro:
                messages.warning(request, f'{erro} Esta é a ficha do Cliente existente.')
                return redirect('clientes:detalhe', pk=erro.cliente.pk)
            except ErroDeNegocio as erro:
                form.add_error('cpf', str(erro))
            else:
                messages.success(request, 'Cliente cadastrado.')
                return redirect('clientes:detalhe', pk=cliente.pk)
        return render(request, 'clientes/form.html', {'form': form})


class DetalheView(PermissaoNecessariaMixin, View):
    permission_required = 'clientes.view_cliente'

    def get(self, request, pk):
        cliente = get_object_or_404(Cliente, pk=pk)
        contexto = {
            'cliente': cliente,
            'beneficios': beneficios_selectors.beneficios_do_cliente(cliente=cliente),
        }
        if request.user.has_perm('clientes.view_historicalcliente'):
            contexto['historico'] = selectors.historico_do_cliente(cliente=cliente)
        return render(request, 'clientes/detalhe.html', contexto)


class EditarView(PermissaoNecessariaMixin, View):
    permission_required = 'clientes.change_cliente'

    def get(self, request, pk):
        cliente = get_object_or_404(Cliente, pk=pk)
        form = ClienteForm(
            initial={'nome': cliente.nome, 'telefone': cliente.telefone, 'email': cliente.email}
        )
        return render(request, 'clientes/form.html', {'form': form, 'cliente': cliente})

    def post(self, request, pk):
        cliente = get_object_or_404(Cliente, pk=pk)
        form = ClienteForm(request.POST)
        if form.is_valid():
            services.editar_cliente(usuario=request.user, cliente=cliente, **form.cleaned_data)
            messages.success(request, 'Dados do Cliente atualizados.')
            return redirect('clientes:detalhe', pk=cliente.pk)
        return render(request, 'clientes/form.html', {'form': form, 'cliente': cliente})


class _MudarSituacaoView(PermissaoNecessariaMixin, View):
    permission_required = 'clientes.change_cliente'
    http_method_names = ['post']
    mensagem = ''

    def executar(self, *, usuario, cliente):
        raise NotImplementedError

    def post(self, request, pk):
        cliente = get_object_or_404(Cliente, pk=pk)
        try:
            self.executar(usuario=request.user, cliente=cliente)
        except ErroDeNegocio as erro:
            messages.error(request, str(erro))
        else:
            messages.success(request, self.mensagem)
        return redirect('clientes:detalhe', pk=cliente.pk)


class InativarView(_MudarSituacaoView):
    mensagem = 'Cliente inativado.'

    def executar(self, *, usuario, cliente):
        services.inativar_cliente(usuario=usuario, cliente=cliente)


class ReativarView(_MudarSituacaoView):
    mensagem = 'Cliente reativado.'

    def executar(self, *, usuario, cliente):
        services.reativar_cliente(usuario=usuario, cliente=cliente)
