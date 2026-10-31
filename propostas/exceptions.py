from core.exceptions import ErroDeNegocio


class BeneficioInativo(ErroDeNegocio):
    def __init__(self):
        super().__init__('O Benefício está inativo; escolha um Benefício ativo.')


class BancoInativo(ErroDeNegocio):
    def __init__(self):
        super().__init__('O Banco está inativo; escolha um Banco ativo.')


class CondicoesInvalidas(ErroDeNegocio):
    pass


class PropostaNaoDigitada(ErroDeNegocio):
    def __init__(self):
        super().__init__('Só é possível enviar ao Banco uma Proposta Digitada.')


class BeneficioSemMargem(ErroDeNegocio):
    def __init__(self):
        super().__init__('O Benefício não tem Margem consignável registrada; registre a consulta.')


class ParcelaAcimaDaMargem(ErroDeNegocio):
    def __init__(self, *, parcela, margem):
        super().__init__(
            f'A parcela (R$ {parcela}) é maior que a Margem vigente (R$ {margem}); '
            'ajuste as condições antes de enviar.'
        )


class MargemAntigaSemConfirmacao(ErroDeNegocio):
    def __init__(self, *, data_consulta):
        super().__init__(
            f'A Margem vigente foi consultada em {data_consulta:%d/%m/%Y}, há mais de '
            '30 dias; confirme para enviar mesmo assim.'
        )


class PropostaTravada(ErroDeNegocio):
    def __init__(self):
        super().__init__('Só é possível alterar as condições de uma Proposta Digitada.')
