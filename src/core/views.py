from django.conf import settings
from django.http import Http404
from django.shortcuts import render

from core.forms import FormularioExemplo


def design(request):
    """Página de referência do design system; só existe com DEBUG ligado."""
    if not settings.DEBUG:
        raise Http404
    com_erros = FormularioExemplo(data={'nome': '', 'banco': 'a', 'valor': 'abc'})
    com_erros.is_valid()
    contexto = {'form_exemplo': FormularioExemplo(), 'form_com_erros': com_erros}
    return render(request, 'design.html', contexto)
