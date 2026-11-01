from django.db import transaction

from contratos.exceptions import MotivoObrigatorio, TransicaoInvalida
from contratos.models import Contrato

# Cada etapa só é marcada a partir da anterior.
ETAPA_ANTERIOR = {
    Contrato.Status.AVERBADO: Contrato.Status.FORMALIZADO,
    Contrato.Status.PAGO: Contrato.Status.AVERBADO,
    Contrato.Status.QUITADO: Contrato.Status.PAGO,
}

# Cancelar só vale quando a averbação ou o pagamento falha.
CANCELAVEIS = {Contrato.Status.FORMALIZADO, Contrato.Status.AVERBADO}


def _salvar(contrato, *, usuario):
    contrato._history_user = usuario
    contrato.save()


@transaction.atomic
def criar_contrato(*, usuario, proposta):
    """Cria o Contrato de uma Proposta, copiando os valores dela."""
    contrato = Contrato(
        proposta=proposta,
        valor=proposta.valor,
        valor_liberado=proposta.valor_liberado,
        prazo=proposta.prazo,
        parcela=proposta.parcela,
        taxa=proposta.taxa,
    )
    _salvar(contrato, usuario=usuario)
    return contrato


@transaction.atomic
def avancar_contrato(*, usuario, contrato, status):
    """Marca Averbado, Pago ou Quitado, na ordem."""
    anterior = ETAPA_ANTERIOR.get(status)
    if anterior is None or contrato.status != anterior:
        raise TransicaoInvalida(
            f'Não é possível marcar essa etapa a partir de {contrato.get_status_display()}.'
        )
    contrato.status = status
    _salvar(contrato, usuario=usuario)
    return contrato


@transaction.atomic
def cancelar_contrato(*, usuario, contrato, motivo):
    """Cancela quando a averbação ou o pagamento falha; o Contrato não reabre."""
    motivo = (motivo or '').strip()
    if not motivo:
        raise MotivoObrigatorio
    if contrato.status not in CANCELAVEIS:
        raise TransicaoInvalida(
            f'Não é possível cancelar um Contrato {contrato.get_status_display()}.'
        )
    contrato.status = Contrato.Status.CANCELADO
    contrato.motivo = motivo
    _salvar(contrato, usuario=usuario)
    return contrato
