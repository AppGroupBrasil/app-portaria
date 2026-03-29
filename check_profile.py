import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'condominio_info.settings')
django.setup()

from info.models import CondominiumProfile

# Check if profile 82 exists
p82 = CondominiumProfile.objects.filter(pk=82).first()
print(f'Profile 82: {p82}')

# Search by email
email_match = CondominiumProfile.objects.filter(email__icontains='guanabaraexpress').values('id','email','condominium_name','is_active','is_testing')
print(f'Email match: {list(email_match)}')

# Search broader
domain_match = CondominiumProfile.objects.filter(email__icontains='guanabara').values('id','email','condominium_name','is_active','is_testing')
print(f'Domain match: {list(domain_match)}')

# Check nearby IDs
nearby = CondominiumProfile.objects.filter(pk__gte=78, pk__lte=86).values('id','email','condominium_name')
print(f'IDs 78-86: {list(nearby)}')

# Check max ID
max_id = CondominiumProfile.objects.order_by('-pk').first()
print(f'Max profile ID: {max_id.pk if max_id else "none"} - {max_id}')

# Search for cargasrec
cargasrec = CondominiumProfile.objects.filter(email__icontains='cargasrec').values('id','email','condominium_name','is_active','is_testing')
print(f'cargasrec match: {list(cargasrec)}')
