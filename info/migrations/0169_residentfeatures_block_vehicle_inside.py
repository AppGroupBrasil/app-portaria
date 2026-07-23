from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('info', '0168_fix_arrived_default_and_leaved_in_nullable'),
    ]

    operations = [
        migrations.AddField(
            model_name='residentfeatures',
            name='block_vehicle_inside',
            field=models.BooleanField(default=False, verbose_name='Bloquear liberação de veículo que consta dentro'),
        ),
    ]
