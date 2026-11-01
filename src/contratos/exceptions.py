from core.exceptions import ErroDeNegocio


class TransicaoInvalida(ErroDeNegocio):
    pass


class DataPagamentoInvalida(ErroDeNegocio):
    pass


class MotivoObrigatorio(ErroDeNegocio):
    def __init__(self):
        super().__init__('Informe o motivo.')
