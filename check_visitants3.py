import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'condominio_info.settings')
django.setup()
from info.models import CondominiumProfile, Resident, Visitant

# Resident 69 is cargasrec@guanabaraexpress.com.br, name=AGNELES GOMES
r = Resident.objects.get(pk=69)
print(f'Resident 69: name="{r.name}", email="{r.email}", apt={r.apartment_id}')

# Profile 82 was deleted. We need to re-create it.
# First check if email cargasrec@guanabaraexpress.com.br is registered anywhere
exists = CondominiumProfile.objects.filter(email='cargasrec@guanabaraexpress.com.br').exists()
print(f'Profile with cargasrec email exists: {exists}')

# Check the other guanabara profiles to understand the pattern
# They are all resident_in=17 (Condominio JMF)
for pid in [83, 84, 85, 86, 87]:
    p = CondominiumProfile.objects.get(pk=pid)
    print(f'Profile {pid}: name="{p.condominium_name}", email="{p.email}", resident_in={p.resident_in_id}, is_active={p.is_active}, is_testing={p.is_testing}')
    # Find matching resident
    matching = Resident.objects.filter(email=p.email).first()
    if matching:
        print(f'  -> Resident match: id={matching.id}, name="{matching.name}", email="{matching.email}"')

# Check what visitants were NOT reaching the portaria
# This means: visitants created by profile that don't have allowed=True or aren't visible to the condominium portaria
# Let's check recent visitants in condo 17 that have plates and are pending
condo17 = CondominiumProfile.objects.get(pk=17)
pending = Visitant.objects.filter(condominium=condo17, allowed=True, arrived=False).order_by('-id')[:20]
print(f'\nPending visitants (allowed but not arrived) in condo 17:')
for v in pending:
    print(f'  id={v.id} name="{v.name}" plate="{v.vehicle_plate}" resident_id={v.resident_id} created={v.created}')
