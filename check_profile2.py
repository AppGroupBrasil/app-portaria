import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'condominio_info.settings')
django.setup()

from info.models import CondominiumProfile, Resident, Visitant, Apartment

# Check if cargasrec exists as Resident
residents = Resident.objects.filter(email__icontains='cargasrec').values('id','name','email','apartment__name','apartment__block__name','apartment__block__condominium__condominium_name')
print(f'Resident cargasrec: {list(residents)}')

# Check all guanabara residents
guanabara_residents = Resident.objects.filter(email__icontains='guanabara').values('id','name','email','apartment__name','apartment__block__name')
print(f'Guanabara residents: {list(guanabara_residents)}')

# Check which condominium guanabara profiles belong to
# Profiles 83-87 are guanabara
for pid in [83, 84, 85, 86, 87]:
    p = CondominiumProfile.objects.filter(pk=pid).first()
    if p:
        # Check if this profile has apartments/blocks
        from info.models import Block
        blocks = Block.objects.filter(condominium=p).values('id','name')
        apts = Apartment.objects.filter(block__condominium=p).values('id','name','block__name')
        print(f'Profile {pid} ({p.email}): blocks={list(blocks)[:3]}, apts={list(apts)[:3]}')

# Check visitants with guanabara-related condominiums
for pid in [83, 84, 85, 86, 87]:
    p = CondominiumProfile.objects.filter(pk=pid).first()
    if p:
        vis_count = Visitant.objects.filter(condominium=p).count()
        if vis_count > 0:
            print(f'Profile {pid} ({p.email}): {vis_count} visitants')
            # Check recent ones
            recent = Visitant.objects.filter(condominium=p).order_by('-id')[:3].values('id','name','vehicle_plate','arrived','allowed','can_leave')
            print(f'  Recent: {list(recent)}')

# Check if cargasrec has any visitants as resident
cargasrec_vis = Visitant.objects.filter(name__icontains='cargasrec').values('id','name','vehicle_plate')
print(f'Visitant named cargasrec: {list(cargasrec_vis)}')

# Also check work_for relationships - maybe profile 82 was an employee profile
# Look for profiles that work_for guanabara profiles
work_for_guanabara = CondominiumProfile.objects.filter(work_for__pk__in=[83,84,85,86,87]).values('id','email','condominium_name','work_for__email')
print(f'Work for guanabara: {list(work_for_guanabara)}')

# Check resident_in relationships
resident_in_guanabara = CondominiumProfile.objects.filter(resident_in__pk__in=[83,84,85,86,87]).values('id','email','condominium_name','resident_in__email')
print(f'Resident in guanabara: {list(resident_in_guanabara)}')
