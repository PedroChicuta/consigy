from beneficios.models import Beneficio, Margem


def beneficios_do_cliente(*, cliente):
    return Beneficio.objects.filter(cliente=cliente).order_by('-ativo', 'numero')


def historico_de_margens(*, beneficio):
    """Margens do Benefício, da consulta mais recente à mais antiga."""
    return Margem.objects.filter(beneficio=beneficio).order_by('-data_consulta', '-pk')


def margem_vigente(*, beneficio):
    """A Margem vigente é a de consulta mais recente."""
    return historico_de_margens(beneficio=beneficio).first()
