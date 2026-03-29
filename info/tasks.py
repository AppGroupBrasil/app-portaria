import pytz
from datetime import date

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.conf import settings

from .models import CondominiumProfile, Contract, Signature

FIXED_TZ = pytz.timezone("America/Sao_Paulo")

def deactivate_expired_users():
    utc_now = timezone.now()
    current_date = utc_now.astimezone(FIXED_TZ).date()
    expired_users = CondominiumProfile.objects.filter(plan_expiration__lt=current_date, is_active=True, is_staff=False)
    expired_users.update(is_active=False)


def notify_expiration():
    utc_now = timezone.now()
    current_date = utc_now.astimezone(FIXED_TZ).date()
    for condominium in CondominiumProfile.objects.filter(is_active=True, is_staff=False):
        for contract in Contract.objects.filter(condominium=condominium, notify_day__exact=current_date):
            _send_email(condominium.condominium_name, contract)


def remove_contracts():
    utc_now = timezone.now()
    current_date = utc_now.astimezone(FIXED_TZ).date()
    for condominium in CondominiumProfile.objects.filter(is_active=True, is_staff=False):
        for contract in Contract.objects.filter(condominium=condominium, notify_day__lt=current_date):
            contract.delete()


def _send_email(condominium, contract):
    try:
        signature = Signature.objects.get(condominium=condominium)
        name = signature.name
        signature_email = signature.email
        whatsapp = signature.whatsapp
        signature_image = signature.image.url

    except Signature.DoesNotExist:
        name = condominium.condominium_name
        signature_email = condominium.email
        whatsapp = condominium.whatsapp
        signature_image = None

    subject = 'Aviso de vencimento de contrato no ' + condominium

    data = {
        'days': contract.days_to_notify,
        'item': contract.item,
        'last_maintenance': contract.last_maintenance,
        'next_maintenance': contract.next_maintenance,
        'current_site': contract.domain,
        'signature': signature,
        'email': signature_email,
        'name': name,
        'whatsapp': whatsapp,
        'signature_image': signature_image,
    }
    if not settings.DEBUG and contract.image:
        data['image'] = "http://" + contract.domain + contract.image.url

    html_content = render_to_string(
        'info/condominium/contract/contract_message.html',
        data
    )

    text_content = strip_tags(html_content)
    msg = EmailMultiAlternatives(subject, text_content, to=[contract.to_email])
    msg.attach_alternative(html_content, "text/html")
    if contract.image:
        msg.attach_file(contract.image.path)
    msg.send()
