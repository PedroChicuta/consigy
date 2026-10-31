from core.exceptions import ErroDeNegocio


class NumeroDuplicado(ErroDeNegocio):
    def __init__(self):
        super().__init__('Já existe um Benefício cadastrado com este número.')


class NumeroInvalido(ErroDeNegocio):
    def __init__(self):
        super().__init__('Informe o número do Benefício.')


class ClienteInativo(ErroDeNegocio):
    def __init__(self):
        super().__init__('O Cliente está inativo; reative-o para cadastrar Benefícios.')


class BeneficioJaInativo(ErroDeNegocio):
    def __init__(self):
        super().__init__('O Benefício já está inativo.')


class BeneficioInativo(ErroDeNegocio):
    def __init__(self):
        super().__init__('O Benefício está inativo; não é possível registrar Margem.')


class MargemInvalida(ErroDeNegocio):
    pass
