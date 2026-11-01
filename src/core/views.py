from django.conf import settings
from django.http import Http404
from django.shortcuts import render


def design(request):
    """Página de referência do design system; só existe com DEBUG ligado."""
    if not settings.DEBUG:
        raise Http404
    return render(request, 'design.html')
