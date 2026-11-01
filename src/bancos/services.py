from django.db import IntegrityError, transaction

from bancos.exceptions import (
    BancoJaAtivo,
    BancoJaInativo,
    CodigoDeBancoDuplicado,
    NomeDeBancoDuplicado,
)
from bancos.models import Banco


def _validar_unicidade(*, nome, codigo, banco=None):
    outros = Banco.objects.all()
    if banco is not None:
        outros = outros.exclude(pk=banco.pk)
    if outros.filter(nome__iexact=nome).exists():
        raise NomeDeBancoDuplicado
    if outros.filter(codigo__iexact=codigo).exists():
        raise CodigoDeBancoDuplicado


def _salvar(banco, *, usuario):
    banco._history_user = usuario
    try:
        with transaction.atomic():
            banco.save()
    except IntegrityError:
        # Corrida com outro cadastro do mesmo nome ou código.
        raise NomeDeBancoDuplicado from None


@transaction.atomic
def criar_banco(*, usuario, nome, codigo):
    nome, codigo = nome.strip(), codigo.strip()
    _validar_unicidade(nome=nome, codigo=codigo)
    banco = Banco(nome=nome, codigo=codigo)
    _salvar(banco, usuario=usuario)
    return banco


@transaction.atomic
def editar_banco(*, usuario, banco, nome, codigo):
    nome, codigo = nome.strip(), codigo.strip()
    _validar_unicidade(nome=nome, codigo=codigo, banco=banco)
    banco.nome = nome
    banco.codigo = codigo
    _salvar(banco, usuario=usuario)
    return banco


@transaction.atomic
def inativar_banco(*, usuario, banco):
    if not banco.ativo:
        raise BancoJaInativo
    banco.ativo = False
    _salvar(banco, usuario=usuario)
    return banco


@transaction.atomic
def reativar_banco(*, usuario, banco):
    if banco.ativo:
        raise BancoJaAtivo
    banco.ativo = True
    _salvar(banco, usuario=usuario)
    return banco
