import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'condominio_info.settings')
django.setup()

from info.models import CondominiumProfile, Resident, Visitant, Apartment, Block

# Check Resident model fields
print('Resident fields:', [f.name for f in Resident._meta.get_fields()])
print('Apartment fields:', [f.name for f in Apartment._meta.get_fields()])
print('Block fields:', [f.name for f in Block._meta.get_fields()])
print()

# Check if cargasrec exists as Resident
residents = Resident.objects.filter(email__icontains='cargasrec')
for r in residents:
    print(f'Resident cargasrec: id={r.id}, name={r.name}, email={r.email}, apt={r.apartment}')

# Check all guanabara residents    
guanabara_residents = Resident.objects.filter(email__icontains='guanabara')
for r in guanabara_residents:
    print(f'Guanabara resident: id={r.id}, name={r.name}, email={r.email}, apt={r.apartment}')

print()
# Check which condominium guanabara profiles manage
for pid in [83, 84, 85, 86, 87]:
    p = CondominiumProfile.objects.filter(pk=pid).first()
    if p:
        blocks = Block.objects.filter(condominium=p)
        vis_count = Visitant.objects.filter(condominium=p).count()
        active_vis = Visitant.objects.filter(condominium=p, arrived=True, leaves_in__isnull=True).count()
        print(f'Profile {pid} ({p.email}): {blocks.count()} blocks, {vis_count} visitants, {active_vis} active')

print()
# Check work_for relationships
work_for_guanabara = CondominiumProfile.objects.filter(work_for__pk__in=[83,84,85,86,87])
for p in work_for_guanabara:
    print(f'Works for guanabara: id={p.id}, email={p.email}, works_for={p.work_for}')

# Check resident_in relationships
resident_in_guanabara = CondominiumProfile.objects.filter(resident_in__pk__in=[83,84,85,86,87])
for p in resident_in_guanabara:
    print(f'Resident in guanabara: id={p.id}, email={p.email}, resident_in={p.resident_in}')

# Check managed_by relationships
managed_by_guanabara = CondominiumProfile.objects.filter(managed_by__pk__in=[83,84,85,86,87])
for p in managed_by_guanabara:
    print(f'Managed by guanabara: id={p.id}, email={p.email}, managed_by={p.managed_by}')
