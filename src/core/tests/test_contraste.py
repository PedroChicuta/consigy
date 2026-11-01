import re
from pathlib import Path

import pytest

import core
from core.contraste import razao_de_contraste

MINIMO_AA = 4.5

# Cores padrão do Bootstrap 5.3.3 (modo claro) que o tema não sobrescreve.
BRANCO = '#ffffff'
TEXTO = '#212529'
SUCESSO = '#198754'
PERIGO = '#dc3545'
AVISO = '#ffc107'

BLOCO_CLARO = re.compile(r":root,\s*\[data-bs-theme='light'\]\s*\{(.*?)\}", re.S)


def _variaveis_do_tema_claro():
    css = (Path(core.__file__).parent / 'static' / 'tema.css').read_text()
    bloco = BLOCO_CLARO.search(css).group(1)
    return dict(re.findall(r'(--[\w-]+):\s*(#[0-9a-fA-F]{6})\s*;', bloco))


def test_contraste_preto_sobre_branco_e_21():
    assert razao_de_contraste('#000000', '#ffffff') == pytest.approx(21)


def test_contraste_e_simetrico_e_igual_a_1_para_cores_iguais():
    assert razao_de_contraste('#14532d', '#14532d') == pytest.approx(1)
    assert razao_de_contraste('#14532d', '#ffffff') == razao_de_contraste('#ffffff', '#14532d')


def _pares_modo_claro():
    v = _variaveis_do_tema_claro()
    return {
        'texto branco sobre primária': (BRANCO, v['--bs-primary']),
        'texto sobre fundo': (TEXTO, BRANCO),
        'link sobre fundo': (v['--bs-link-color'], BRANCO),
        'link (hover) sobre fundo': (v['--bs-link-hover-color'], BRANCO),
        'texto primário enfatizado sobre fundo sutil': (
            v['--bs-primary-text-emphasis'],
            v['--bs-primary-bg-subtle'],
        ),
        'texto branco sobre sucesso': (BRANCO, SUCESSO),
        'texto branco sobre perigo': (BRANCO, PERIGO),
        'texto escuro sobre aviso': (TEXTO, AVISO),
    }


@pytest.mark.parametrize('par', list(_pares_modo_claro()))
def test_pares_do_modo_claro_atendem_wcag_aa(par):
    frente, fundo = _pares_modo_claro()[par]

    razao = razao_de_contraste(frente, fundo)

    assert razao >= MINIMO_AA, f'modo claro, {par}: {frente} sobre {fundo} = {razao:.2f}:1'
