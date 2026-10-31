from core.exceptions import ErroDeNegocio


class NomeDeBancoDuplicado(ErroDeNegocio):
    def __init__(self):
        super().__init__('Já existe um Banco com este nome.')


class CodigoDeBancoDuplicado(ErroDeNegocio):
    def __init__(self):
        super().__init__('Já existe um Banco com este código.')


class BancoJaInativo(ErroDeNegocio):
    def __init__(self):
        super().__init__('O Banco já está inativo.')


class BancoJaAtivo(ErroDeNegocio):
    def __init__(self):
        super().__init__('O Banco já está ativo.')
