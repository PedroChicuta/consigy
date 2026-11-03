import re
from decimal import Decimal, InvalidOperation

_TABELA_NUMERO_BR = str.maketrans(',.', '.,')
_CARACTERES_TELEFONE = re.compile(r'^[\d\s().-]+$')


def formatar_moeda(valor):
    """Formata um valor numérico como moeda brasileira (`R$ 25.000,00`)."""
    if valor is None or valor == '':
        return ''
    if isinstance(valor, bool):
        return str(valor)
    if isinstance(valor, Decimal):
        quantia = valor
    else:
        try:
            quantia = Decimal(str(valor).strip())
        except InvalidOperation:
            return str(valor)
    if not quantia.is_finite():
        return str(valor)
    sinal = '-' if quantia < 0 else ''
    numero = f'{abs(quantia):,.2f}'.translate(_TABELA_NUMERO_BR)
    return f'{sinal}R$ {numero}'


def formatar_telefone(valor):
    """Formata telefones de 10 ou 11 dígitos no padrão brasileiro, preservando outros tamanhos."""
    if valor is None or valor == '':
        return ''
    texto = str(valor)
    if not _CARACTERES_TELEFONE.match(texto):
        return texto
    digitos = re.sub(r'\D', '', texto)
    if len(digitos) == 11:
        return f'({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}'
    if len(digitos) == 10:
        return f'({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}'
    return texto
