from bancos.models import Banco


def listar_bancos():
    """Todos os Bancos, ativos e inativos, para a consulta da lista."""
    return Banco.objects.all()


def bancos_ativos():
    """Bancos disponíveis como escolha para novas Propostas."""
    return Banco.objects.filter(ativo=True)
