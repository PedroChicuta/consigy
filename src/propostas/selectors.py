from django.db.models import Q

from clientes.cpf import normalizar_cpf
from core.formatacao import formatar_moeda
from propostas.models import Modalidade, Proposta


def listar_modalidades():
    """Todas as Modalidades, ativas e inativas, para a consulta da lista."""
    return Modalidade.objects.all()


def modalidades_ativas():
    """Modalidades disponíveis como escolha para novas Propostas."""
    return Modalidade.objects.filter(ativo=True)


def _base():
    return Proposta.objects.select_related('beneficio__cliente', 'banco', 'modalidade', 'operador')


def listar_propostas(*, status='', banco=None, cliente='', modalidade=None):
    """Propostas da equipe, filtradas por status, Banco e Modalidade (pk) e Cliente (nome/CPF)."""
    propostas = _base()
    if status:
        propostas = propostas.filter(status=status)
    if modalidade:
        propostas = propostas.filter(modalidade_id=modalidade)
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


def impedimento_envio(*, proposta):
    """Retorna o impedimento ou pendência para envio de uma Proposta Digitada, ou None."""
    if proposta.status != Proposta.Status.DIGITADA:
        return None
    margem = proposta.beneficio.margem_vigente
    if margem is None:
        return {
            'tipo': 'sem_margem',
            'nivel': 'warning',
            'mensagem': (
                'O Benefício não possui Margem consignável registrada; '
                'registre uma consulta antes de enviar ao Banco.'
            ),
        }
    if proposta.parcela > margem.valor:
        return {
            'tipo': 'parcela_acima_da_margem',
            'nivel': 'danger',
            'mensagem': (
                f'A parcela ({formatar_moeda(proposta.parcela)}) é maior que a Margem vigente '
                f'({formatar_moeda(margem.valor)}); ajuste as condições antes de enviar ao Banco.'
            ),
        }
    if margem.antiga:
        return {
            'tipo': 'margem_antiga',
            'nivel': 'warning',
            'mensagem': (
                f'A Margem vigente foi consultada em {margem.data_consulta:%d/%m/%Y}, há mais de '
                '30 dias; confirme para enviar mesmo assim.'
            ),
        }
    return None

