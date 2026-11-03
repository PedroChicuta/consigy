from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from accounts.permissions import PermissaoNecessariaMixin
from beneficios import selectors, services
from beneficios.forms import BeneficioForm, MargemForm
from beneficios.models import Beneficio
from clientes.models import Cliente
from core.exceptions import ErroDeNegocio


class CriarView(PermissaoNecessariaMixin, View):
    permission_required = 'beneficios.add_beneficio'
    acoes_extras = [
        {
            'rotulo': 'Salvar e criar Proposta',
            'valor': 'salvar_criar_proposta',
            'estilo': 'btn-outline-primary',
        }
    ]

    def get(self, request, cliente_pk):
        cliente = get_object_or_404(Cliente, pk=cliente_pk)
        return render(
            request,
            'beneficios/form.html',
            {
                'form': BeneficioForm(),
                'cliente': cliente,
                'acoes_extras': self.acoes_extras,
            },
        )

    def post(self, request, cliente_pk):
        cliente = get_object_or_404(Cliente, pk=cliente_pk)
        form = BeneficioForm(request.POST)
        if form.is_valid():
            try:
                beneficio = services.criar_beneficio(
                    usuario=request.user,
                    cliente=cliente,
                    **form.cleaned_data,
                )
            except ErroDeNegocio as erro:
                form.add_error(None, str(erro))
            else:
                messages.success(request, 'Benefício cadastrado.')
                if request.POST.get('acao') == 'salvar_criar_proposta':
                    return redirect(f"{reverse('propostas:criar')}?beneficio={beneficio.pk}")
                return redirect('clientes:detalhe', pk=cliente.pk)
        return render(
            request,
            'beneficios/form.html',
            {
                'form': form,
                'cliente': cliente,
                'acoes_extras': self.acoes_extras,
            },
        )


def _contexto_detalhe(beneficio, form=None):
    return {
        'beneficio': beneficio,
        'margem_vigente': selectors.margem_vigente(beneficio=beneficio),
        'margens': selectors.historico_de_margens(beneficio=beneficio),
        'form': form or MargemForm(),
    }


class DetalheView(PermissaoNecessariaMixin, View):
    permission_required = 'beneficios.view_beneficio'

    def get(self, request, pk):
        beneficio = get_object_or_404(Beneficio.objects.select_related('cliente'), pk=pk)
        return render(request, 'beneficios/detalhe.html', _contexto_detalhe(beneficio))


class RegistrarMargemView(PermissaoNecessariaMixin, View):
    permission_required = 'beneficios.add_margem'
    http_method_names = ['post']

    def post(self, request, pk):
        beneficio = get_object_or_404(Beneficio.objects.select_related('cliente'), pk=pk)
        form = MargemForm(request.POST)
        if form.is_valid():
            try:
                services.registrar_margem(
                    usuario=request.user, beneficio=beneficio, **form.cleaned_data
                )
            except ErroDeNegocio as erro:
                form.add_error(None, str(erro))
            else:
                messages.success(request, 'Margem registrada.')
                return redirect('beneficios:detalhe', pk=beneficio.pk)
        return render(request, 'beneficios/detalhe.html', _contexto_detalhe(beneficio, form))


class InativarView(PermissaoNecessariaMixin, View):
    permission_required = 'beneficios.change_beneficio'
    http_method_names = ['post']

    def post(self, request, pk):
        beneficio = get_object_or_404(Beneficio, pk=pk)
        try:
            services.inativar_beneficio(usuario=request.user, beneficio=beneficio)
        except ErroDeNegocio as erro:
            messages.error(request, str(erro))
        else:
            messages.success(request, 'Benefício inativado.')
        return redirect('clientes:detalhe', pk=beneficio.cliente_id)
