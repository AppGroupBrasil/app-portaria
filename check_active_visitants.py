import django, os
os.environ["DJANGO_SETTINGS_MODULE"] = "condominio_info.settings"
django.setup()
from info.models import Visitant

active = Visitant.objects.filter(leaves_in__isnull=True).count()
total = Visitant.objects.count()
print(f"Total: {total}, Active(no leaves_in): {active}")
for r in Visitant.objects.order_by("-id")[:10].values("id","name","vehicle_plate","arrived","leaves_in","visit_in"):
    print(r)
