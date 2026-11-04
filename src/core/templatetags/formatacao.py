from django import template

from core.formatacao import formatar_moeda, formatar_telefone

register = template.Library()


@register.filter(name='moeda')
def moeda(valor):
    return formatar_moeda(valor)


@register.filter(name='telefone')
def telefone(valor):
    return formatar_telefone(valor)
