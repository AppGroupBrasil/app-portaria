import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'condominio_info.settings')
django.setup()

from info.models import CondominiumProfile, Resident, Visitant, Apartment, Block

# Which condominium owns apartment 17?
apt = Apartment.objects.get(pk=17)
block = apt.block
condo = block.condominium
print(f'Apartment 17: number={apt.number}, complement={apt.complement}')
print(f'Block: id={block.id}, name={block.name}')
print(f'Condominium: id={condo.id}, name={condo.condominium_name}, email={condo.email}')
print(f'Condo is_active={condo.is_active}, is_testing={condo.is_testing}')

# Check resident 69
r = Resident.objects.get(pk=69)
print(f'\nResident 69: name={r.name}, email={r.email}, kind={r.kind}')

# Check if resident 69 has a linked CondominiumProfile (resident_in)
linked_profile = CondominiumProfile.objects.filter(email='cargasrec@guanabaraexpress.com.br').first()
print(f'Linked profile: {linked_profile}')

# Check profiles with resident_in pointing to this condo
resident_profiles = CondominiumProfile.objects.filter(resident_in=condo)
for p in resident_profiles:
    print(f'Profile resident_in condo: id={p.id}, email={p.email}, condominium_name={p.condominium_name}')

# Check visitants sent by this resident
visitants_by_resident = Visitant.objects.filter(resident=r)
print(f'\nVisitants by resident 69: {visitants_by_resident.count()}')
for v in visitants_by_resident.order_by('-id')[:5]:
    print(f'  Visitant id={v.id}, name={v.name}, plate={v.vehicle_plate}, arrived={v.arrived}, allowed={v.allowed}, can_leave={v.can_leave}, condominium={v.condominium}')

# Check visitants for this condominium
total_vis = Visitant.objects.filter(condominium=condo).count()
active_vis = Visitant.objects.filter(condominium=condo, arrived=True, leaves_in__isnull=True).count()
pending_vis = Visitant.objects.filter(condominium=condo, allowed=False, arrived=False).count()
print(f'\nCondominium total visitants: {total_vis}')
print(f'Active (arrived, no exit): {active_vis}')
print(f'Pending (not allowed, not arrived): {pending_vis}')

# Check recent visitants for this condo
recent = Visitant.objects.filter(condominium=condo).order_by('-id')[:10]
for v in recent:
    print(f'  Recent: id={v.id}, name={v.name}, plate={v.vehicle_plate}, arrived={v.arrived}, allowed={v.allowed}, can_leave={v.can_leave}')
