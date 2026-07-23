from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('info', '0169_residentfeatures_block_vehicle_inside'),
    ]

    operations = [
        migrations.AddField(
            model_name='residentfeatures',
            name='auto_visitant_leave',
            field=models.BooleanField(default=False, verbose_name='Liberação automática de visitantes'),
        ),
    ]
