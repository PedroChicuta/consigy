from django.db.models import Q

from clientes.cpf import normalizar_cpf
from contratos.models import Contrato


def contratos_da_proposta(*, proposta):
    return Contrato.objects.select_related('proposta__banco').filter(proposta=proposta)


def contratos_do_cliente(*, cliente):
    return Contrato.objects.select_related(
        'proposta__beneficio__cliente', 'proposta__banco'
    ).filter(proposta__beneficio__cliente=cliente)


def listar_contratos(*, status='', cliente=''):
    """Contratos filtrados por status e por Cliente (nome ou CPF)."""
    contratos = Contrato.objects.select_related('proposta__beneficio__cliente', 'proposta__banco')
    if status:
        contratos = contratos.filter(status=status)
    cliente = (cliente or '').strip()
    if cliente:
        filtro = Q(proposta__beneficio__cliente__nome__icontains=cliente)
        digitos = normalizar_cpf(cliente)
        if digitos:
            filtro |= Q(proposta__beneficio__cliente__cpf__contains=digitos)
        contratos = contratos.filter(filtro)
    return contratos


def historico_do_contrato(*, contrato):
    """Mudanças de status, da mais nova à mais antiga, com autor e data."""
    registros = list(
        contrato.history.select_related('history_user').order_by('-history_date', '-pk')
    )
    return [
        r
        for i, r in enumerate(registros)
        if i + 1 == len(registros) or registros[i + 1].status != r.status
    ]
