from django.db import transaction

from contratos.models import Contrato


@transaction.atomic
def criar_contrato(*, usuario, proposta):
    """Cria o Contrato de uma Proposta, copiando os valores dela."""
    contrato = Contrato(
        proposta=proposta,
        valor=proposta.valor,
        prazo=proposta.prazo,
        parcela=proposta.parcela,
        taxa=proposta.taxa,
    )
    contrato._history_user = usuario
    contrato.save()
    return contrato
