import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'condominio_info.settings')
django.setup()

from django.db.models import Count
from info.models import Visitant, VisitantReport

# 1. Placas com muitos registros de Visitant (mais de 20)
print("=" * 70)
print("PLACAS COM MUITOS REGISTROS NA TABELA VISITANT (>20)")
print("=" * 70)
plates = (Visitant.objects
    .exclude(vehicle_plate__isnull=True)
    .exclude(vehicle_plate='')
    .values('vehicle_plate')
    .annotate(total=Count('id'))
    .filter(total__gt=20)
    .order_by('-total'))

for p in plates:
    plate = p['vehicle_plate']
    arrived = Visitant.objects.filter(vehicle_plate__iexact=plate, arrived=True).count()
    reports = VisitantReport.objects.filter(vehicle_plate__iexact=plate).count()
    print(f"  Placa: {plate:10s} | Visitants: {p['total']:5d} | Arrived: {arrived:3d} | Reports: {reports:6d}")

# 2. Placas com muitos relatórios duplicados (mais de 100)
print()
print("=" * 70)
print("PLACAS COM MUITOS REPORTS DUPLICADOS (>100)")
print("=" * 70)
report_plates = (VisitantReport.objects
    .exclude(vehicle_plate__isnull=True)
    .exclude(vehicle_plate='')
    .values('vehicle_plate')
    .annotate(total=Count('id'))
    .filter(total__gt=100)
    .order_by('-total'))

for p in report_plates:
    print(f"  Placa: {p['vehicle_plate']:10s} | Reports: {p['total']:6d}")

print()
print("=" * 70)
print("RESUMO")
print("=" * 70)
total_reports = VisitantReport.objects.count()
total_visitants = Visitant.objects.count()
print(f"  Total Visitants: {total_visitants}")
print(f"  Total Reports: {total_reports}")
