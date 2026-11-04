from django.db.models import Prefetch, Q

from beneficios.models import Beneficio, Margem
from clientes.cpf import normalizar_cpf

MIN_DIGITOS_CPF = 3


def beneficios_do_cliente(*, cliente):
    return (
        Beneficio.objects.filter(cliente=cliente)
        .prefetch_related(
            Prefetch('margens', queryset=Margem.objects.order_by('-data_consulta', '-pk'))
        )
        .order_by('-ativo', 'numero')
    )


def historico_de_margens(*, beneficio):
    """Margens do Benefício, da consulta mais recente à mais antiga."""
    return Margem.objects.filter(beneficio=beneficio).order_by('-data_consulta', '-pk')


def margem_vigente(*, beneficio):
    """A Margem vigente é a de consulta mais recente."""
    return historico_de_margens(beneficio=beneficio).first()


def buscar_beneficios_ativos(*, busca=''):
    """Benefícios ativos de Clientes ativos por CPF, nome do Cliente ou número do Benefício."""
    busca = (busca or '').strip()
    if not busca:
        return Beneficio.objects.none()

    filtro = Q(cliente__nome__icontains=busca)
    digitos = ''.join(c for c in busca if c.isalnum())
    if digitos:
        filtro |= Q(numero__icontains=digitos)
    cpf_digitos = normalizar_cpf(busca)
    if len(cpf_digitos) >= MIN_DIGITOS_CPF:
        filtro |= Q(cliente__cpf__contains=cpf_digitos)

    return (
        Beneficio.objects.filter(ativo=True, cliente__ativo=True)
        .filter(filtro)
        .select_related('cliente')
        .prefetch_related(
            Prefetch('margens', queryset=Margem.objects.order_by('-data_consulta', '-pk'))
        )
        .order_by('cliente__nome', 'numero')
        .distinct()
    )

