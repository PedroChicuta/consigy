from django.contrib.auth.management import create_permissions
from django.db import migrations

PERMISSOES_OPERADOR = ['add_proposta', 'change_proposta', 'view_proposta']
PERMISSOES_SUPERVISOR = PERMISSOES_OPERADOR + ['view_historicalproposta']


def atribuir_permissoes(apps, schema_editor):
    # As permissões só são criadas no post_migrate; aqui garantimos que existam.
    app_config = apps.get_app_config('propostas')
    app_config.models_module = True
    create_permissions(app_config, apps=apps, verbosity=0)

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    for nome, codenames in (
        ('Operador', PERMISSOES_OPERADOR),
        ('Supervisor', PERMISSOES_SUPERVISOR),
    ):
        grupo = Group.objects.get(name=nome)
        grupo.permissions.add(
            *Permission.objects.filter(content_type__app_label='propostas', codename__in=codenames)
        )


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0002_grupos_operador_supervisor'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('propostas', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(atribuir_permissoes, migrations.RunPython.noop),
    ]
