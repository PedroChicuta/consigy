from django.db import IntegrityError, transaction

from clientes.cpf import cpf_valido, normalizar_cpf
from clientes.exceptions import ClienteJaAtivo, ClienteJaInativo, CpfDuplicado, CpfInvalido
from clientes.models import Cliente


def _salvar(cliente, *, usuario):
    cliente._history_user = usuario
    cliente.save()


@transaction.atomic
def criar_cliente(*, usuario, nome, cpf, data_nascimento, telefone, email=''):
    cpf = normalizar_cpf(cpf)
    if not cpf_valido(cpf):
        raise CpfInvalido
    existente = Cliente.objects.filter(cpf=cpf).first()
    if existente:
        raise CpfDuplicado(existente)
    cliente = Cliente(
        nome=nome, cpf=cpf, data_nascimento=data_nascimento, telefone=telefone, email=email
    )
    try:
        with transaction.atomic():
            _salvar(cliente, usuario=usuario)
    except IntegrityError:
        # Corrida com outro cadastro do mesmo CPF.
        raise CpfDuplicado(Cliente.objects.get(cpf=cpf)) from None
    return cliente


@transaction.atomic
def editar_cliente(*, usuario, cliente, nome, telefone, email=''):
    cliente.nome = nome
    cliente.telefone = telefone
    cliente.email = email
    _salvar(cliente, usuario=usuario)
    return cliente


@transaction.atomic
def inativar_cliente(*, usuario, cliente):
    if not cliente.ativo:
        raise ClienteJaInativo
    cliente.ativo = False
    _salvar(cliente, usuario=usuario)
    return cliente


@transaction.atomic
def reativar_cliente(*, usuario, cliente):
    if cliente.ativo:
        raise ClienteJaAtivo
    cliente.ativo = True
    _salvar(cliente, usuario=usuario)
    return cliente
