from core.exceptions import ErroDeNegocio


class CpfInvalido(ErroDeNegocio):
    def __init__(self):
        super().__init__('CPF inválido. Confira os dígitos informados.')


class CpfDuplicado(ErroDeNegocio):
    def __init__(self, cliente):
        self.cliente = cliente
        super().__init__('Já existe um Cliente cadastrado com este CPF.')


class ClienteJaInativo(ErroDeNegocio):
    def __init__(self):
        super().__init__('O Cliente já está inativo.')


class ClienteJaAtivo(ErroDeNegocio):
    def __init__(self):
        super().__init__('O Cliente já está ativo.')
