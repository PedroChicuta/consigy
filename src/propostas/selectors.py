from django.db.models import Q

from clientes.cpf import normalizar_cpf
from propostas.models import Proposta


def _base():
    return Proposta.objects.select_related('beneficio__cliente', 'banco', 'operador')


def listar_propostas(*, status='', banco=None, cliente=''):
    """Propostas de toda a equipe, filtradas por status, Banco (pk) e Cliente (nome ou CPF)."""
    propostas = _base()
    if status:
        propostas = propostas.filter(status=status)
    if banco:
        propostas = propostas.filter(banco_id=banco)
    cliente = (cliente or '').strip()
    if cliente:
        filtro = Q(beneficio__cliente__nome__icontains=cliente)
        digitos = normalizar_cpf(cliente)
        if digitos:
            filtro |= Q(beneficio__cliente__cpf__contains=digitos)
        propostas = propostas.filter(filtro)
    return propostas


def propostas_do_cliente(*, cliente):
    return _base().filter(beneficio__cliente=cliente)


def historico_da_proposta(*, proposta):
    """Mudanças de status, da mais nova à mais antiga, com autor e data."""
    registros = list(
        proposta.history.select_related('history_user').order_by('-history_date', '-pk')
    )
    resultado = []
    for i, registro in enumerate(registros):
        anterior = registros[i + 1] if i + 1 < len(registros) else None
        if anterior is None or anterior.status != registro.status:
            resultado.append(registro)
    return resultado
