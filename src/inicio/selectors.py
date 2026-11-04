from django.db.models import Count, Q

from clientes.cpf import cpf_valido, normalizar_cpf
from clientes.models import Cliente
from contratos.models import Contrato
from propostas.models import Proposta

MIN_DIGITOS_CPF = 3

STATUS_PROPOSTAS_EM_ANDAMENTO = [
    Proposta.Status.DIGITADA,
    Proposta.Status.ENVIADA,
    Proposta.Status.EM_ANALISE,
    Proposta.Status.AGUARDANDO_SALDO,
    Proposta.Status.PORTABILIDADE_AUTORIZADA,
    Proposta.Status.APROVADA,
]

STATUS_CONTRATOS_PENDENTES = [
    Contrato.Status.FORMALIZADO,
    Contrato.Status.AVERBADO,
]


def buscar_clientes_atendimento(*, busca=''):
    """Busca rápida de Clientes por CPF ou nome com contagem de Benefícios ativos."""
    busca = (busca or '').strip()
    if not busca:
        return Cliente.objects.none()

    filtro = Q(nome__icontains=busca)
    digitos = normalizar_cpf(busca)
    if digitos and len(digitos) >= MIN_DIGITOS_CPF:
        filtro |= Q(cpf__contains=digitos)

    return (
        Cliente.objects.filter(filtro)
        .annotate(total_beneficios_ativos=Count('beneficios', filter=Q(beneficios__ativo=True)))
        .order_by('nome')
        .distinct()
    )


def verificar_cpf_inedito(*, busca=''):
    """Devolve os 11 dígitos do CPF se a busca for um CPF válido e inexistente no banco."""
    digitos = normalizar_cpf(busca)
    if cpf_valido(digitos) and not Cliente.objects.filter(cpf=digitos).exists():
        return digitos
    return None


def listar_propostas_em_andamento(*, usuario=None, apenas_minhas=False):
    """Propostas abertas da equipe ou do próprio operador."""
    propostas = (
        Proposta.objects.select_related('beneficio__cliente', 'banco', 'modalidade', 'operador')
        .filter(status__in=STATUS_PROPOSTAS_EM_ANDAMENTO)
        .order_by('-criado_em', '-pk')
    )
    if apenas_minhas and usuario:
        propostas = propostas.filter(operador=usuario)
    return propostas


def listar_contratos_pendentes():
    """Contratos aguardando averbação ou pagamento."""
    return (
        Contrato.objects.select_related(
            'proposta__beneficio__cliente', 'proposta__banco', 'modalidade'
        )
        .filter(status__in=STATUS_CONTRATOS_PENDENTES)
        .order_by('-criado_em', '-pk')
    )


def definir_escopo_padrao_propostas(*, usuario):
    """Determina o filtro padrão de Propostas: 'todas' para Supervisor, 'minhas' para os demais."""
    if usuario and usuario.is_authenticated and usuario.groups.filter(name='Supervisor').exists():
        return 'todas'
    return 'minhas'
