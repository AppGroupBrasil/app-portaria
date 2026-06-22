import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'condominio_info.settings'
django.setup()

from info.models import CondominiumProfile
from datetime import date

total = CondominiumProfile.objects.count()
active = CondominiumProfile.objects.filter(is_active=True).count()
inactive = CondominiumProfile.objects.filter(is_active=False).count()
expired = CondominiumProfile.objects.filter(plan_expiration__lte=date.today(), is_active=True).count()
no_plan = CondominiumProfile.objects.filter(plan_expiration__isnull=True, is_active=True).count()

print(f"Total: {total}")
print(f"Ativos: {active}")
print(f"Inativos: {inactive}")
print(f"Expirados (ativos mas plano vencido): {expired}")
print(f"Sem plano (ativos): {no_plan}")

# Mostrar ultimos 10 inativos
print("\n--- Ultimos 10 inativos ---")
for u in CondominiumProfile.objects.filter(is_active=False).order_by('-id')[:10]:
    print(f"  id={u.id} nome={u.condominium_name} email={u.email} plano_exp={u.plan_expiration}")
