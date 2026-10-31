from core.exceptions import ErroDeNegocio


class BeneficioInativo(ErroDeNegocio):
    def __init__(self):
        super().__init__('O Benefício está inativo; escolha um Benefício ativo.')


class BancoInativo(ErroDeNegocio):
    def __init__(self):
        super().__init__('O Banco está inativo; escolha um Banco ativo.')


class CondicoesInvalidas(ErroDeNegocio):
    pass


class PropostaTravada(ErroDeNegocio):
    def __init__(self):
        super().__init__('Só é possível alterar as condições de uma Proposta Digitada.')
