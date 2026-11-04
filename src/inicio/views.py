from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.views.decorators.http import require_GET

from inicio import selectors


@require_GET
def index(request):
    if request.headers.get('HX-Request'):
        if 'q' in request.GET:
            return buscar_clientes(request)
        if 'propostas' in request.GET or 'filtro_propostas' in request.GET:
            return fila_propostas(request)

    filtro_propostas = request.GET.get('propostas') or request.GET.get('filtro_propostas')
    if filtro_propostas not in ('minhas', 'todas'):
        filtro_propostas = selectors.definir_escopo_padrao_propostas(usuario=request.user)

    propostas = []
    if request.user.is_authenticated and request.user.has_perm('propostas.view_proposta'):
        propostas = selectors.listar_propostas_em_andamento(
            usuario=request.user, apenas_minhas=(filtro_propostas == 'minhas')
        )

    contratos = []
    if request.user.is_authenticated and request.user.has_perm('contratos.view_contrato'):
        contratos = selectors.listar_contratos_pendentes()

    return render(
        request,
        'inicio/index.html',
        {
            'filtro_propostas': filtro_propostas,
            'propostas': propostas,
            'contratos': contratos,
        },
    )


@require_GET
def buscar_clientes(request):
    if not request.user.is_authenticated or not request.user.has_perm('clientes.view_cliente'):
        raise PermissionDenied

    busca = request.GET.get('q', '').strip()
    clientes = selectors.buscar_clientes_atendimento(busca=busca)
    cpf_inedito = selectors.verificar_cpf_inedito(busca=busca)

    return render(
        request,
        'inicio/partials/_resultado_busca.html',
        {
            'busca': busca,
            'clientes': clientes,
            'cpf_inedito': cpf_inedito,
        },
    )


@require_GET
def fila_propostas(request):
    if not request.user.is_authenticated or not request.user.has_perm('propostas.view_proposta'):
        raise PermissionDenied

    filtro_propostas = request.GET.get('propostas') or request.GET.get('filtro_propostas')
    if filtro_propostas not in ('minhas', 'todas'):
        filtro_propostas = selectors.definir_escopo_padrao_propostas(usuario=request.user)

    propostas = selectors.listar_propostas_em_andamento(
        usuario=request.user, apenas_minhas=(filtro_propostas == 'minhas')
    )

    return render(
        request,
        'inicio/partials/_fila_propostas.html',
        {
            'filtro_propostas': filtro_propostas,
            'propostas': propostas,
        },
    )
