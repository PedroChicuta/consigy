from django.db import transaction

from beneficios.selectors import margem_vigente
from propostas.exceptions import (
    BancoInativo,
    BeneficioInativo,
    BeneficioSemMargem,
    CondicoesInvalidas,
    MargemAntigaSemConfirmacao,
    ParcelaAcimaDaMargem,
    PropostaNaoDigitada,
    PropostaTravada,
)
from propostas.models import Proposta

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
def criar_proposta(*, usuario, beneficio, banco, valor, prazo, parcela, taxa, observacoes=''):
    if not beneficio.ativo:
        raise BeneficioInativo
    if not banco.ativo:
        raise BancoInativo
    _validar_condicoes(valor=valor, prazo=prazo, parcela=parcela, taxa=taxa)
    proposta = Proposta(
        beneficio=beneficio,
        banco=banco,
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
    *, usuario, proposta, beneficio, banco, valor, prazo, parcela, taxa, observacoes=''
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
    _validar_condicoes(valor=valor, prazo=prazo, parcela=parcela, taxa=taxa)
    proposta.beneficio = beneficio
    proposta.banco = banco
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
