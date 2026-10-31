from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('contratos', '0002_permissoes_dos_grupos'),
    ]

    operations = [
        migrations.AddField(
            model_name='contrato',
            name='motivo',
            field=models.TextField(blank=True, verbose_name='motivo do cancelamento'),
        ),
        migrations.AddField(
            model_name='historicalcontrato',
            name='motivo',
            field=models.TextField(blank=True, verbose_name='motivo do cancelamento'),
        ),
    ]
