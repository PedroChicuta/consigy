from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import resolve_url


class LoginObrigatorioMiddleware:
    """Exige sessão autenticada em qualquer endereço, exceto a tela de login.

    Estáticos são servidos pelo whitenoise, que responde antes deste middleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated and request.path != resolve_url(settings.LOGIN_URL):
            return redirect_to_login(request.get_full_path(), resolve_url(settings.LOGIN_URL))
        return self.get_response(request)
