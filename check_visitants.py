import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'condominio_info.settings')
django.setup()
from info.models import Resident, Visitant
r = Resident.objects.get(pk=69)
vis = Visitant.objects.filter(resident=r)
print('Total visitants by resident 69:', vis.count())
for v in vis.order_by('-id')[:10]:
    print(f'  id={v.id} name={v.name} plate={v.vehicle_plate} arrived={v.arrived} allowed={v.allowed} can_leave={v.can_leave} condo_id={v.condominium_id}')

# Check the _vehicle_plate_active logic for this resident's condominium
from info.models import CondominiumProfile
condo = CondominiumProfile.objects.get(pk=17)
# Check if there are active (arrived not exited) visitants blocking new ones
active_plates = Visitant.objects.filter(
    condominium=condo,
    arrived=True,
    leaves_in__isnull=True,
    allowed=True
).values_list('vehicle_plate', flat=True).distinct()
print(f'\nActive plates in condo 17: {list(active_plates)[:20]}')
print(f'Total active plates: {active_plates.count()}')
