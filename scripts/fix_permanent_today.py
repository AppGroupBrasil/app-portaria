"""
Converte as autorizacoes de Visitant criadas hoje que estao como
'permanentes' (until == condominium.plan_expiration) para terminar
hoje as 23:59:59 (horario local).

Uso:
    python manage.py shell < scripts/fix_permanent_today.py
"""
from datetime import datetime, time
from django.utils import timezone
from info.models import Visitant

now = timezone.localtime()
today = now.date()
end_of_day = timezone.make_aware(datetime.combine(today, time(23, 59, 59)))

qs = Visitant.objects.filter(created__date=today).select_related("condominium")
alterados = 0
for v in qs:
    pe = v.condominium.plan_expiration
    if v.until and pe and v.until.date() == pe:
        v.until = end_of_day
        v.save(update_fields=["until"])
        alterados += 1

print(f"Visitants alterados: {alterados} (data {today}, novo until {end_of_day})")
