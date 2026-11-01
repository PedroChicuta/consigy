def _canal_linear(canal):
    c = canal / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminancia(cor):
    """Luminância relativa WCAG de uma cor '#rrggbb'."""
    cor = cor.lstrip('#')
    r, g, b = (_canal_linear(int(cor[i : i + 2], 16)) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def razao_de_contraste(cor_a, cor_b):
    """Razão de contraste WCAG (1 a 21) entre duas cores '#rrggbb'."""
    claro, escuro = sorted((luminancia(cor_a), luminancia(cor_b)), reverse=True)
    return (claro + 0.05) / (escuro + 0.05)
