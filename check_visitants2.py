import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'condominio_info.settings')
django.setup()
from info.models import CondominiumProfile, Visitant

# The guanabara profiles are residents (resident_in) of condo 17
# Check profile 83 (digitacaorec@guanabaraexpress.com.br) - one of the guanabara users
# These users create visitants as resident profiles

# Find if cargasrec had a profile that was profile 82
# Profile 82 doesn't exist. Let's check if there's a profile that belongs to cargasrec@guanabaraexpress.com.br
# Already confirmed: no profile with that email exists.
# Let's verify what profile 82 was - check visitants created by resident=82
vis_by_82 = Visitant.objects.filter(resident_id=82)
print(f'Visitants created by profile 82: {vis_by_82.count()}')
for v in vis_by_82.order_by('-id')[:5]:
    print(f'  id={v.id} name={v.name} plate={v.vehicle_plate} condo_id={v.condominium_id}')

# Check if there's a CondominiumProfile that was recently deleted
from django.contrib.auth import get_user_model
User = get_user_model()

# Check all profiles near ID 82
for pid in range(80, 90):
    p = CondominiumProfile.objects.filter(pk=pid).first()
    if p:
        print(f'Profile {pid}: {p.email} - {p.condominium_name} (active={p.is_active}, resident_in={p.resident_in_id})')
    else:
        print(f'Profile {pid}: DELETED')

# Check if the user tried to register cargasrec@guanabaraexpress.com.br as a login profile
# But it might have been already deleted
# Let's check the Django auth_user table for ID 82
print()
# Check visitants with no plate that are recent in condo 17
condo17 = CondominiumProfile.objects.get(pk=17)
no_plate_vis = Visitant.objects.filter(condominium=condo17, vehicle_plate='').order_by('-id')[:10]
print(f'Recent visitants without plate in condo 17:')
for v in no_plate_vis:
    print(f'  id={v.id} name={v.name} plate="{v.vehicle_plate}" arrived={v.arrived} allowed={v.allowed} resident_id={v.resident_id}')

# Check active visitants that might be blocking
active_vis = Visitant.objects.filter(condominium=condo17, arrived=True, leaves_in__isnull=True, allowed=True).count()
print(f'\nTotal active visitants (arrived, no exit, allowed) in condo 17: {active_vis}')

# Check if our new _vehicle_plate_active is blocking this user
# The resident creates an entry => _vehicle_plate_active checks same plate active in same condo
# If placeholder plates or empty plates are the issue...
plate_check = Visitant.objects.filter(condominium=condo17, arrived=True, leaves_in__isnull=True, allowed=True, vehicle_plate='').count()
print(f'Active visitants with empty plate: {plate_check}')
