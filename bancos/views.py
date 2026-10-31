from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from accounts.permissions import PermissaoNecessariaMixin
from bancos import selectors, services
from bancos.forms import BancoForm
from bancos.models import Banco
from core.exceptions import ErroDeNegocio


class ListaView(PermissaoNecessariaMixin, View):
    permission_required = 'bancos.view_banco'

    def get(self, request):
        return render(request, 'bancos/lista.html', {'bancos': selectors.listar_bancos()})


class CriarView(PermissaoNecessariaMixin, View):
    permission_required = 'bancos.add_banco'

    def get(self, request):
        return render(request, 'bancos/form.html', {'form': BancoForm()})

    def post(self, request):
        form = BancoForm(request.POST)
        if form.is_valid():
            try:
                services.criar_banco(usuario=request.user, **form.cleaned_data)
            except ErroDeNegocio as erro:
                form.add_error(None, str(erro))
            else:
                messages.success(request, 'Banco cadastrado.')
                return redirect('bancos:lista')
        return render(request, 'bancos/form.html', {'form': form})


class EditarView(PermissaoNecessariaMixin, View):
    permission_required = 'bancos.change_banco'

    def get(self, request, pk):
        banco = get_object_or_404(Banco, pk=pk)
        form = BancoForm(initial={'nome': banco.nome, 'codigo': banco.codigo})
        return render(request, 'bancos/form.html', {'form': form, 'banco': banco})

    def post(self, request, pk):
        banco = get_object_or_404(Banco, pk=pk)
        form = BancoForm(request.POST)
        if form.is_valid():
            try:
                services.editar_banco(usuario=request.user, banco=banco, **form.cleaned_data)
            except ErroDeNegocio as erro:
                form.add_error(None, str(erro))
            else:
                messages.success(request, 'Banco atualizado.')
                return redirect('bancos:lista')
        return render(request, 'bancos/form.html', {'form': form, 'banco': banco})


class _MudarSituacaoView(PermissaoNecessariaMixin, View):
    permission_required = 'bancos.change_banco'
    http_method_names = ['post']
    mensagem = ''

    def executar(self, *, usuario, banco):
        raise NotImplementedError

    def post(self, request, pk):
        banco = get_object_or_404(Banco, pk=pk)
        try:
            self.executar(usuario=request.user, banco=banco)
        except ErroDeNegocio as erro:
            messages.error(request, str(erro))
        else:
            messages.success(request, self.mensagem)
        return redirect('bancos:lista')


class InativarView(_MudarSituacaoView):
    mensagem = 'Banco inativado.'

    def executar(self, *, usuario, banco):
        services.inativar_banco(usuario=usuario, banco=banco)


class ReativarView(_MudarSituacaoView):
    mensagem = 'Banco reativado.'

    def executar(self, *, usuario, banco):
        services.reativar_banco(usuario=usuario, banco=banco)
