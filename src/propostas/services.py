from django.db import transaction

from beneficios.selectors import margem_vigente
from contratos.services import criar_contrato
from propostas.exceptions import (
    BancoInativo,
    BeneficioInativo,
    BeneficioSemMargem,
    CancelamentoSemPermissao,
    CondicoesInvalidas,
    MargemAntigaSemConfirmacao,
    ModalidadeInativa,
    MotivoObrigatorio,
    ParcelaAcimaDaMargem,
    PropostaNaoDigitada,
    PropostaTravada,
    TransicaoInvalida,
)
from propostas.models import FINAIS, Proposta

CAMPOS_POSITIVOS = {
    'valor': 'O valor',
    'prazo': 'O prazo',
    'parcela': 'A parcela',
    'taxa': 'A taxa',
}


def _salvar(proposta, *, usuario):
    proposta._history_user = usuario
    proposta.save()


def _validar_condicoes(*, valor, prazo, parcela, taxa):
    informados = {'valor': valor, 'prazo': prazo, 'parcela': parcela, 'taxa': taxa}
    for campo, rotulo in CAMPOS_POSITIVOS.items():
        if informados[campo] <= 0:
            raise CondicoesInvalidas(f'{rotulo} deve ser maior que zero.')


@transaction.atomic
def criar_proposta(
    *, usuario, beneficio, banco, modalidade, valor, prazo, parcela, taxa, observacoes=''
):
    if not beneficio.ativo:
        raise BeneficioInativo
    if not banco.ativo:
        raise BancoInativo
    if not modalidade.ativo:
        raise ModalidadeInativa
    _validar_condicoes(valor=valor, prazo=prazo, parcela=parcela, taxa=taxa)
    proposta = Proposta(
        beneficio=beneficio,
        banco=banco,
        modalidade=modalidade,
        operador=usuario,
        valor=valor,
        prazo=prazo,
        parcela=parcela,
        taxa=taxa,
        observacoes=observacoes,
    )
    _salvar(proposta, usuario=usuario)
    return proposta


@transaction.atomic
def editar_proposta(
    *, usuario, proposta, beneficio, banco, modalidade, valor, prazo, parcela, taxa, observacoes=''
):
    """Altera as condições e as observações; só vale enquanto a Proposta está Digitada."""
    if proposta.status != Proposta.Status.DIGITADA:
        raise PropostaTravada
    # Só exige ativo quando a escolha mudou: um Banco inativado depois da digitação
    # não impede ajustar o restante.
    if beneficio != proposta.beneficio and not beneficio.ativo:
        raise BeneficioInativo
    if banco != proposta.banco and not banco.ativo:
        raise BancoInativo
    if modalidade != proposta.modalidade and not modalidade.ativo:
        raise ModalidadeInativa
    _validar_condicoes(valor=valor, prazo=prazo, parcela=parcela, taxa=taxa)
    proposta.beneficio = beneficio
    proposta.banco = banco
    proposta.modalidade = modalidade
    proposta.valor = valor
    proposta.prazo = prazo
    proposta.parcela = parcela
    proposta.taxa = taxa
    proposta.observacoes = observacoes
    _salvar(proposta, usuario=usuario)
    return proposta


@transaction.atomic
def enviar_proposta(*, usuario, proposta, confirmar_margem_antiga=False):
    """Envia a Proposta ao Banco, desde que a parcela caiba na Margem vigente."""
    if proposta.status != Proposta.Status.DIGITADA:
        raise PropostaNaoDigitada
    margem = margem_vigente(beneficio=proposta.beneficio)
    if margem is None:
        raise BeneficioSemMargem
    if proposta.parcela > margem.valor:
        raise ParcelaAcimaDaMargem(parcela=proposta.parcela, margem=margem.valor)
    if margem.antiga and not confirmar_margem_antiga:
        raise MargemAntigaSemConfirmacao(data_consulta=margem.data_consulta)
    proposta.status = Proposta.Status.ENVIADA
    _salvar(proposta, usuario=usuario)
    return proposta


@transaction.atomic
def editar_observacoes(*, usuario, proposta, observacoes):
    """As observações podem ser editadas em qualquer etapa."""
    proposta.observacoes = observacoes
    _salvar(proposta, usuario=usuario)
    return proposta


# Cada etapa só é marcada a partir da anterior.
ETAPA_ANTERIOR = {
    Proposta.Status.EM_ANALISE: Proposta.Status.ENVIADA,
    Proposta.Status.APROVADA: Proposta.Status.EM_ANALISE,
}


@transaction.atomic
def avancar_proposta(*, usuario, proposta, status):
    """Marca Em análise ou Aprovada, na ordem."""
    anterior = ETAPA_ANTERIOR.get(status)
    if anterior is None or proposta.status != anterior:
        raise TransicaoInvalida(
            f'Não é possível marcar essa etapa a partir de {proposta.get_status_display()}.'
        )
    proposta.status = status
    _salvar(proposta, usuario=usuario)
    return proposta


@transaction.atomic
def formalizar_proposta(*, usuario, proposta):
    """Formaliza uma Proposta Aprovada e cria, na mesma operação, o Contrato dela."""
    if proposta.status != Proposta.Status.APROVADA:
        raise TransicaoInvalida(
            f'Só é possível formalizar uma Proposta Aprovada; esta está '
            f'{proposta.get_status_display()}.'
        )
    proposta.status = Proposta.Status.FORMALIZADA
    _salvar(proposta, usuario=usuario)
    return criar_contrato(usuario=usuario, proposta=proposta)


def _encerrar(*, usuario, proposta, status, motivo):
    motivo = (motivo or '').strip()
    if not motivo:
        raise MotivoObrigatorio
    if proposta.status in FINAIS:
        raise TransicaoInvalida(f'A Proposta já está {proposta.get_status_display()}.')
    proposta.status = status
    proposta.motivo = motivo
    _salvar(proposta, usuario=usuario)
    return proposta


@transaction.atomic
def recusar_proposta(*, usuario, proposta, motivo):
    """O Banco recusou; vale de qualquer etapa antes de Formalizada."""
    return _encerrar(
        usuario=usuario, proposta=proposta, status=Proposta.Status.RECUSADA, motivo=motivo
    )


@transaction.atomic
def cancelar_proposta(*, usuario, proposta, motivo):
    """Desistência. Depois de Aprovada, só quem tem a permissão de Supervisor cancela."""
    if proposta.status == Proposta.Status.APROVADA and not usuario.has_perm(
        'propostas.cancelar_proposta_aprovada'
    ):
        raise CancelamentoSemPermissao
    return _encerrar(
        usuario=usuario, proposta=proposta, status=Proposta.Status.CANCELADA, motivo=motivo
    )
