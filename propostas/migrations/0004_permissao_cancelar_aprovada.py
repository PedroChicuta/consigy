from django.contrib.auth.management import create_permissions
from django.db import migrations


def atribuir_permissao(apps, schema_editor):
    app_config = apps.get_app_config('propostas')
    app_config.models_module = True
    create_permissions(app_config, apps=apps, verbosity=0)

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    Group.objects.get(name='Supervisor').permissions.add(
        Permission.objects.get(
            content_type__app_label='propostas', codename='cancelar_proposta_aprovada'
        )
    )


class Migration(migrations.Migration):
    dependencies = [
        ('propostas', '0003_motivo_e_cancelar_aprovada'),
    ]

    operations = [
        migrations.RunPython(atribuir_permissao, migrations.RunPython.noop),
    ]
