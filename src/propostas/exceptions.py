from core.exceptions import ErroDeNegocio
from core.formatacao import formatar_moeda


class BeneficioInativo(ErroDeNegocio):
    def __init__(self):
        super().__init__('O Benefício está inativo; escolha um Benefício ativo.')


class BancoInativo(ErroDeNegocio):
    def __init__(self):
        super().__init__('O Banco está inativo; escolha um Banco ativo.')


class ModalidadeInativa(ErroDeNegocio):
    def __init__(self):
        super().__init__('A Modalidade está inativa; escolha uma Modalidade ativa.')


class NomeDeModalidadeObrigatorio(ErroDeNegocio):
    def __init__(self):
        super().__init__('Informe o nome da Modalidade.')


class NomeDeModalidadeDuplicado(ErroDeNegocio):
    def __init__(self):
        super().__init__('Já existe uma Modalidade com este nome.')


class ModalidadeJaInativa(ErroDeNegocio):
    def __init__(self):
        super().__init__('A Modalidade já está inativa.')


class ModalidadeJaAtiva(ErroDeNegocio):
    def __init__(self):
        super().__init__('A Modalidade já está ativa.')


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
            f'A parcela ({formatar_moeda(parcela)}) é maior que a Margem vigente '
            f'({formatar_moeda(margem)}); ajuste as condições antes de enviar.'
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


class TransicaoInvalida(ErroDeNegocio):
    pass


class MotivoObrigatorio(ErroDeNegocio):
    def __init__(self):
        super().__init__('Informe o motivo.')


class CancelamentoSemPermissao(ErroDeNegocio):
    def __init__(self):
        super().__init__('Só o Supervisor pode cancelar uma Proposta Aprovada.')
