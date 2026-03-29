import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'condominio_info.settings')
django.setup()
from info.models import CondominiumProfile, Resident
from datetime import date, timedelta

# Check if the profile already exists
exists = CondominiumProfile.objects.filter(email='cargasrec@guanabaraexpress.com.br').exists()
if exists:
    print('Profile already exists! No action needed.')
    p = CondominiumProfile.objects.get(email='cargasrec@guanabaraexpress.com.br')
    print(f'Profile: id={p.id}, name={p.condominium_name}, email={p.email}, resident_in={p.resident_in_id}, is_active={p.is_active}')
    exit()

# Get the resident data
r = Resident.objects.get(pk=69)
print(f'Resident: name="{r.name}", email="{r.email}"')

# Get the condominium (Condomínio JMF, id=17)
condo = CondominiumProfile.objects.get(pk=17)
print(f'Condominium: id={condo.id}, name={condo.condominium_name}')
print(f'Condo plan_expiration: {condo.plan_expiration}')

# Use profile 83 as reference (same guanabara pattern)
ref_profile = CondominiumProfile.objects.get(pk=83)
print(f'Reference profile 83: is_active={ref_profile.is_active}, is_testing={ref_profile.is_testing}, plan_expiration={ref_profile.plan_expiration}')

# Create the new profile
new_profile = CondominiumProfile()
new_profile.email = 'cargasrec@guanabaraexpress.com.br'
new_profile.condominium_name = r.name  # AGNELES GOMES
new_profile.set_password('1234')       # Default password
new_profile.is_active = True
new_profile.is_testing = True
new_profile.is_staff = False
new_profile.is_administrator = False
new_profile.resident_in = condo
new_profile.plan_expiration = condo.plan_expiration
new_profile.profile = 'resident'
new_profile.save()

print(f'\nProfile CREATED: id={new_profile.id}, email={new_profile.email}, name={new_profile.condominium_name}')
print(f'resident_in={new_profile.resident_in_id}, is_active={new_profile.is_active}')
print(f'Password set to: 1234')
