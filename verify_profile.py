import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'condominio_info.settings')
django.setup()
from info.models import CondominiumProfile

p = CondominiumProfile.objects.get(email='cargasrec@guanabaraexpress.com.br')
print(f'id={p.id}, email={p.email}, name={p.condominium_name}')
print(f'plan_expiration={p.plan_expiration}, is_active={p.is_active}')
print(f'resident_in={p.resident_in_id}, is_testing={p.is_testing}')
print(f'profile={p.profile}')

# Check the condominium's actual plan_expiration
condo = CondominiumProfile.objects.get(pk=17)
print(f'\nCondominium plan_expiration={condo.plan_expiration}, is_active={condo.is_active}')

# The profile was created, now verify login would work
# Check that resident name+email matches
from info.models import Resident
try:
    res = Resident.objects.get(name=p.condominium_name, email=p.email)
    print(f'\nResident match found: id={res.id}, name={res.name}, apt_id={res.apartment_id}')
    print('The user CAN create visitants (resident lookup will work)')
except Resident.DoesNotExist:
    print('\nWARNING: No Resident matches this profile! User cannot create visitants.')
    # Try case-insensitive
    res2 = Resident.objects.filter(email__iexact=p.email).first()
    if res2:
        print(f'Found case-insensitive: id={res2.id}, name="{res2.name}", email="{res2.email}"')
