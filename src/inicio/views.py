from django.shortcuts import render


def index(request):
    contexto = {'nome': 'operador'}
    if request.htmx:
        return render(request, 'inicio/partials/_saudacao.html', contexto)
    return render(request, 'inicio/index.html', contexto)
