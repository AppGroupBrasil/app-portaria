from django.db import migrations
from django.db.models import Count

LOGINVESTE_NAME = "LOGINVESTE"


def _loginveste(apps):
    """Cadastro ativo do Loginveste: o homonimo com mais visitantes registrados."""
    CondominiumProfile = apps.get_model('info', 'CondominiumProfile')
    candidates = [
        c for c in CondominiumProfile.objects.annotate(total=Count('visitant'))
        if (c.condominium_name or "").strip().upper() == LOGINVESTE_NAME
    ]
    if not candidates:
        return None
    condominium = max(candidates, key=lambda c: c.total)
    if not condominium.total:
        return None
    return condominium


def enable(apps, schema_editor):
    ResidentFeatures = apps.get_model('info', 'ResidentFeatures')
    condominium = _loginveste(apps)
    if condominium is None:
        return
    features = ResidentFeatures.objects.filter(condominium=condominium).first()
    if features is None:
        ResidentFeatures.objects.create(condominium=condominium, auto_visitant_leave=True)
        return
    ResidentFeatures.objects.filter(pk=features.pk).update(auto_visitant_leave=True)


def disable(apps, schema_editor):
    ResidentFeatures = apps.get_model('info', 'ResidentFeatures')
    condominium = _loginveste(apps)
    if condominium is None:
        return
    ResidentFeatures.objects.filter(condominium=condominium).update(auto_visitant_leave=False)


class Migration(migrations.Migration):

    dependencies = [
        ('info', '0170_residentfeatures_auto_visitant_leave'),
    ]

    operations = [
        migrations.RunPython(enable, disable),
    ]
