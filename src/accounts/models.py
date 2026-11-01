from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Usuário do sistema (Operador de backoffice). Customizado desde a primeira migration."""
