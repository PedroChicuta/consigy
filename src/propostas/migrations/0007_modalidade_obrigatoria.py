import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('propostas', '0006_modalidades_iniciais'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proposta',
            name='modalidade',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='propostas',
                to='propostas.modalidade',
            ),
        ),
    ]
