import re
from pathlib import Path

import pytest

import core
from core.contraste import razao_de_contraste

MINIMO_AA = 4.5

# Cores padrão do Bootstrap 5.3.3 que o tema não sobrescreve.
BRANCO = '#ffffff'
PRETO = '#000000'
SUCESSO = '#198754'
PERIGO = '#dc3545'
AVISO = '#ffc107'

# Texto e fundo do corpo em cada modo (padrão do Bootstrap).
CORPO = {
    'claro': {'texto': '#212529', 'fundo': '#ffffff'},
    'escuro': {'texto': '#dee2e6', 'fundo': '#212529'},
}

BLOCOS = {
    'claro': re.compile(r":root,\s*\[data-bs-theme='light'\]\s*\{(.*?)\}", re.S),
    'escuro': re.compile(r'^\[data-bs-theme="dark"\]\s*\{(.*?)\}', re.S | re.M),
}


def _variaveis_do_tema(modo):
    css = (Path(core.__file__).parent / 'static' / 'tema.css').read_text()
    bloco = BLOCOS[modo].search(css).group(1)
    return dict(re.findall(r'(--[\w-]+):\s*(#[0-9a-fA-F]{6})\s*;', bloco))


def test_contraste_preto_sobre_branco_e_21():
    assert razao_de_contraste(PRETO, BRANCO) == pytest.approx(21)


def test_contraste_e_simetrico_e_igual_a_1_para_cores_iguais():
    assert razao_de_contraste('#14532d', '#14532d') == pytest.approx(1)
    assert razao_de_contraste('#14532d', BRANCO) == razao_de_contraste(BRANCO, '#14532d')


def _pares(modo):
    v = _variaveis_do_tema(modo)
    texto, fundo = CORPO[modo]['texto'], CORPO[modo]['fundo']
    return {
        'texto branco sobre primária': (BRANCO, v['--bs-primary']),
        'texto sobre fundo': (texto, fundo),
        'link sobre fundo': (v['--bs-link-color'], fundo),
        'link (hover) sobre fundo': (v['--bs-link-hover-color'], fundo),
        'texto primário enfatizado sobre fundo sutil': (
            v['--bs-primary-text-emphasis'],
            v['--bs-primary-bg-subtle'],
        ),
        'texto branco sobre sucesso': (BRANCO, SUCESSO),
        'texto branco sobre perigo': (BRANCO, PERIGO),
        'texto escuro sobre aviso': (PRETO, AVISO),
    }


@pytest.mark.parametrize('modo', list(BLOCOS))
@pytest.mark.parametrize('par', list(_pares('claro')))
def test_pares_atendem_wcag_aa(modo, par):
    frente, fundo = _pares(modo)[par]

    razao = razao_de_contraste(frente, fundo)

    assert razao >= MINIMO_AA, f'modo {modo}, {par}: {frente} sobre {fundo} = {razao:.2f}:1'
