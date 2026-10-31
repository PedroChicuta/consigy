import datetime
from decimal import Decimal

from django.db import IntegrityError, transaction

from beneficios.exceptions import (
    BeneficioInativo,
    BeneficioJaInativo,
    ClienteInativo,
    MargemInvalida,
    NumeroDuplicado,
    NumeroInvalido,
)
from beneficios.models import Beneficio, Margem


def _salvar(objeto, *, usuario):
    objeto._history_user = usuario
    objeto.save()


def _normalizar_numero(numero):
    return ''.join(c for c in (numero or '') if c.isalnum())


@transaction.atomic
def criar_beneficio(*, usuario, cliente, numero, especie):
    if not cliente.ativo:
        raise ClienteInativo
    numero = _normalizar_numero(numero)
    if not numero:
        raise NumeroInvalido
    if Beneficio.objects.filter(numero=numero).exists():
        raise NumeroDuplicado
    beneficio = Beneficio(cliente=cliente, numero=numero, especie=especie)
    try:
        with transaction.atomic():
            _salvar(beneficio, usuario=usuario)
    except IntegrityError:
        # Corrida com outro cadastro do mesmo número.
        raise NumeroDuplicado from None
    return beneficio


@transaction.atomic
def inativar_beneficio(*, usuario, beneficio):
    if not beneficio.ativo:
        raise BeneficioJaInativo
    beneficio.ativo = False
    _salvar(beneficio, usuario=usuario)
    return beneficio


@transaction.atomic
def registrar_margem(*, usuario, beneficio, valor, data_consulta):
    if not beneficio.ativo:
        raise BeneficioInativo
    if Decimal(valor) <= 0:
        raise MargemInvalida('A Margem deve ser maior que zero.')
    if data_consulta > datetime.date.today():
        raise MargemInvalida('A data da consulta não pode estar no futuro.')
    margem = Margem(beneficio=beneficio, valor=valor, data_consulta=data_consulta)
    _salvar(margem, usuario=usuario)
    return margem
