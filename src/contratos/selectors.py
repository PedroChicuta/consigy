from django.db.models import Q

from clientes.cpf import normalizar_cpf
from contratos.models import Contrato


def contratos_da_proposta(*, proposta):
    return Contrato.objects.select_related('proposta__banco').filter(proposta=proposta)


def contratos_do_cliente(*, cliente):
    return Contrato.objects.select_related(
        'proposta__beneficio__cliente', 'proposta__banco'
    ).filter(proposta__beneficio__cliente=cliente)


def listar_contratos(*, status='', cliente='', pago_de=None, pago_ate=None, modalidade=None):
    """Contratos filtrados por status, Modalidade (pk), Cliente (nome/CPF) e data de pagamento."""
    contratos = Contrato.objects.select_related(
        'proposta__beneficio__cliente', 'proposta__banco', 'modalidade'
    )
    if status:
        contratos = contratos.filter(status=status)
    if modalidade:
        contratos = contratos.filter(modalidade_id=modalidade)
    if pago_de:
        contratos = contratos.filter(data_pagamento__gte=pago_de)
    if pago_ate:
        contratos = contratos.filter(data_pagamento__lte=pago_ate)
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
