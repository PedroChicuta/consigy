from django.db import migrations, models


def copiar_valor(apps, schema_editor):
    """Registros antigos ficam com Valor liberado igual ao valor do Contrato."""
    for nome in ('Contrato', 'HistoricalContrato'):
        apps.get_model('contratos', nome).objects.update(valor_liberado=models.F('valor'))


class Migration(migrations.Migration):
    dependencies = [
        ('contratos', '0004_permissao_change_operador'),
        ('propostas', '0008_valor_liberado'),
    ]

    operations = [
        migrations.AddField(
            model_name='contrato',
            name='valor_liberado',
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=12, verbose_name='valor liberado (R$)'
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='historicalcontrato',
            name='valor_liberado',
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=12, verbose_name='valor liberado (R$)'
            ),
            preserve_default=False,
        ),
        migrations.RunPython(copiar_valor, migrations.RunPython.noop),
    ]
