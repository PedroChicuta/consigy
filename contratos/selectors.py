from contratos.models import Contrato


def contratos_da_proposta(*, proposta):
    return Contrato.objects.select_related('proposta__banco').filter(proposta=proposta)


def contratos_do_cliente(*, cliente):
    return Contrato.objects.select_related(
        'proposta__beneficio__cliente', 'proposta__banco'
    ).filter(proposta__beneficio__cliente=cliente)
