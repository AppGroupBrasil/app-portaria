import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'condominio_info.settings')
django.setup()

from info.models import Visitant, VisitantReport

plate = 'kgq1h70'
total = Visitant.objects.filter(vehicle_plate__iexact=plate).count()
arrived = Visitant.objects.filter(vehicle_plate__iexact=plate, arrived=True).count()
not_arrived = Visitant.objects.filter(vehicle_plate__iexact=plate, arrived=False).count()
no_visit = Visitant.objects.filter(vehicle_plate__iexact=plate, visit_in__isnull=True).count()
no_name = Visitant.objects.filter(vehicle_plate__iexact=plate, name__isnull=True).count()
empty_name = Visitant.objects.filter(vehicle_plate__iexact=plate, name='').count()

print(f'Total visitants with plate: {total}')
print(f'Arrived (arrived=True): {arrived}')
print(f'Not arrived (arrived=False): {not_arrived}')
print(f'No visit_in (NULL): {no_visit}')
print(f'Name is NULL: {no_name}')
print(f'Name is empty string: {empty_name}')
print()
print('--- Currently arrived visitants ---')
for v in Visitant.objects.filter(vehicle_plate__iexact=plate, arrived=True):
    print(f'  ID={v.pk}, name="{v.name}", apartment={v.apartment}, block={v.block}, visit_in={v.visit_in}, can_leave={v.can_leave}')

print()
print(f'--- Reports with plate: {VisitantReport.objects.filter(vehicle_plate__iexact=plate).count()} ---')
