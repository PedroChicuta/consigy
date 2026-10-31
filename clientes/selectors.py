from django.db.models import Q

from clientes.cpf import normalizar_cpf
from clientes.models import Cliente

# Abaixo disso, dígitos soltos casariam CPFs demais para servir de busca.
MIN_DIGITOS_CPF = 3


def listar_clientes(*, busca=''):
    """Clientes filtrados por parte do nome ou do CPF (com ou sem máscara).

    Dígitos também casam com o número de algum Benefício do Cliente.
    """
    clientes = Cliente.objects.all()
    busca = (busca or '').strip()
    if not busca:
        return clientes
    filtro = Q(nome__icontains=busca)
    # CPF só se a busca parece um CPF (dígitos e pontuação), não um nome com número.
    if all(c.isdigit() or c in '.-' for c in busca):
        digitos = normalizar_cpf(busca)
        if len(digitos) >= MIN_DIGITOS_CPF:
            filtro |= Q(cpf__contains=digitos) | Q(beneficios__numero__contains=digitos)
    return clientes.filter(filtro).distinct()


def historico_do_cliente(*, cliente):
    """Registros do histórico, do mais novo ao mais antigo, com as mudanças de cada um."""
    registros = list(
        cliente.history.select_related('history_user').order_by('-history_date', '-pk')
    )
    resultado = []
    for i, registro in enumerate(registros):
        anterior = registros[i + 1] if i + 1 < len(registros) else None
        mudancas = registro.diff_against(anterior).changes if anterior else []
        resultado.append({'registro': registro, 'mudancas': mudancas})
    return resultado
