import re


def normalizar_cpf(valor):
    """Devolve só os dígitos do CPF informado (com ou sem pontos e traço)."""
    return re.sub(r'\D', '', valor or '')


def _digito(base):
    soma = sum(int(d) * peso for d, peso in zip(base, range(len(base) + 1, 1, -1), strict=True))
    resto = (soma * 10) % 11
    return str(0 if resto == 10 else resto)


def cpf_valido(cpf):
    """Valida um CPF já normalizado (11 dígitos) pelos dígitos verificadores."""
    if len(cpf) != 11 or not cpf.isdigit() or cpf == cpf[0] * 11:
        return False
    primeiro = _digito(cpf[:9])
    return cpf[9] == primeiro and cpf[10] == _digito(cpf[:9] + primeiro)


def formatar_cpf(cpf):
    return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'


def mascarar_cpf(cpf):
    return f'***.{cpf[3:6]}.{cpf[6:9]}-**'
