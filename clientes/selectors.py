from clientes.models import Cliente


def listar_clientes():
    return Cliente.objects.all()


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
