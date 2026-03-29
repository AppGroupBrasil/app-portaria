# import geocoder
import datetime
import pytz

from io import BytesIO

import qrcode
from django.contrib.auth.models import Permission
from django.core.files import File
from django.utils.html import strip_tags
from geoip2 import database
from geoip2.errors import AddressNotFoundError
from geoip2.errors import GeoIP2Error
from geopy.geocoders import OpenCage

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_str, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from info.models import CondominiumProfile, UserLocation, Signature, Notification, UserControl

FIXED_TZ = pytz.timezone("America/Sao_Paulo")

class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
                str(user.is_active) + str(user.pk) + str(timestamp)
        )


def get_user_from_email_verification_token(self, token: str):
    try:
        uid = force_str(urlsafe_base64_decode(self))
        user = CondominiumProfile.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError,
            CondominiumProfile.DoesNotExist):
        return None

    email_verification_token = EmailVerificationTokenGenerator()
    if user is not None and email_verification_token.check_token(user, token):
        return user
    return None


def send_notification_email(request, user):
    # email_verification_token = EmailVerificationTokenGenerator()
    current_site = get_current_site(request)
    subject = 'Novo cadastro no App Portaria'
    body = render_to_string(
        'info/admin/new_user_notification.html',
        {
            'domain': current_site.domain,
            'name': user.condominium_name,
            'email': user.email,
            'expiration': user.plan_expiration,
        }
    )
    EmailMessage(to=[settings.EMAIL_ADMIN_NOTIFICATION], subject=subject, body=body).send()


def send_verification_email(request, user):
    email_verification_token = EmailVerificationTokenGenerator()
    current_site = get_current_site(request)
    subject = 'Ativação da sua conta Resolvido Info'
    # data = add_signature_to_data(request)
    data = {'domain': current_site.domain, 'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': email_verification_token.make_token(user)}
    body = render_to_string(
        'info/condominium/account/email_verification.html',
        data
    )
    text_content = strip_tags(body)
    msg = EmailMultiAlternatives(subject, text_content, to=[user.email])
    msg.attach_alternative(body, "text/html")
    msg.send()


def _get_user_location(ip_address):
    geoip_reader = database.Reader(settings.GEOIP_PATH + 'GeoLite2-City.mmdb')
    print(ip_address)
    try:
        response = geoip_reader.city(ip_address)
        location = {
            'country': response.country.name,
            'city': response.city.name,
            'latitude': response.location.latitude,
            'longitude': response.location.longitude
        }

    except AddressNotFoundError:
        print("address not found error")
        location = None
    except GeoIP2Error:
        # Handle any errors related to the GeoLite2 database file
        print("Geo IP2 Error")
        location = None
    return location


def check_in(request, condominium, latitude, longitude):
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('HTTP_CLIENT_IP')

    if not ip_address:
        ip_address = '127.0.0.1'

    if latitude and longitude:
        user_location = UserLocation()
        user_location.condominium = condominium
        user_location.country = 'country'
        user_location.city = 'city'
        user_location.latitude = latitude
        user_location.longitude = longitude
        user_location.ip_address = ip_address
        user_location.address = reverse_geocode(latitude=user_location.latitude, longitude=user_location.longitude)
        user_location.save()
        return user_location

    location = _get_user_location(ip_address)
    user_location = UserLocation()
    user_location.condominium = condominium
    user_location.country = location.get('country')
    user_location.city = location.get('city')
    user_location.latitude = location.get('latitude')
    user_location.longitude = location.get('longitude')
    user_location.ip_address = ip_address
    user_location.address = reverse_geocode(latitude=user_location.latitude, longitude=user_location.longitude)
    user_location.save()

    return user_location


def user_check_in(request, condominium, latitude, longitude):
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('HTTP_CLIENT_IP')

    if not ip_address:
        ip_address = '127.0.0.1'

    if latitude and longitude:
        user_control = UserControl()
        user_control.condominium = condominium
        user_control.country = 'country'
        user_control.city = 'city'
        user_control.latitude = latitude
        user_control.longitude = longitude
        user_control.ip_address = ip_address
        user_control.address = reverse_geocode(latitude=user_control.latitude, longitude=user_control.longitude)
        user_control.user = CondominiumProfile.objects.get(pk=int(request.user.id))
        user_control.check_in = datetime.datetime.now(FIXED_TZ)
        user_control.check_out = None
        user_control.save()

        return user_control

    location = _get_user_location(ip_address)
    user_control = UserControl()
    user_control.condominium = condominium
    user_control.country = location.get('country')
    user_control.city = location.get('city')
    user_control.latitude = location.get('latitude')
    user_control.longitude = location.get('longitude')
    user_control.ip_address = ip_address
    user_control.address = reverse_geocode(latitude=user_control.latitude, longitude=user_control.longitude)
    user_control.user = CondominiumProfile.objects.get(pk=int(request.user.id))
    user_control.check_in = datetime.datetime.now(FIXED_TZ)
    user_control.check_out = None
    user_control.save()

    return user_control


def reverse_geocode(latitude, longitude):
    geolocator = OpenCage(api_key="b93c214d6a344cad93451d68eace268a")
    location = geolocator.reverse((latitude, longitude), exactly_one=True)
    if location:
        return location.address
    else:
        return None


def get_condominium(request):
    condominium = CondominiumProfile.objects.get(pk=request.user.id)

    if condominium.selected:
        return CondominiumProfile.objects.get(pk=condominium.selected)

    work_for = condominium.get_boss()
    if work_for:
        return work_for

    resides_in = condominium.get_reside_in()
    if resides_in:
        return resides_in

    return condominium


def add_signature_to_data(request):

    condominium = get_condominium(request)
    user = CondominiumProfile.objects.get(pk=int(request.user.id))

    try:
        signature = Signature.objects.get(condominium=condominium)
        name = signature.name
        signature_email = signature.email
        whatsapp = signature.whatsapp
        signature_image = signature.image.url

    except Signature.DoesNotExist:
        signature = None
        name = user.condominium_name
        signature_email = user.email
        whatsapp = user.whatsapp
        signature_image = None

    data = {
        'current_site': get_current_site(request),
        'signature': signature,
        'email': signature_email,
        'name': name,
        'whatsapp': whatsapp,
        'signature_image': signature_image,
    }

    return data


def add_notification(condominium, to_list, message, request=None, url=None):
    for email in to_list:
        try:
            receiver = CondominiumProfile.objects.get(resident_in=condominium, email=email)
            notification = Notification()
            notification.condominium = condominium
            notification.receiver = receiver
            notification.message = message
            notification.title = 'Notificação de ' + condominium.condominium_name
            notification.url = url
            notification.save()

            if request:

                subject = 'Notificação de ' + condominium.condominium_name
                data = add_signature_to_data(request)
                data['message'] = message
                data['domain'] = get_current_site(request).domain
                html_content = render_to_string(
                    'info/condominium/reservation/notification_message.html',
                    data
                )

                text_content = strip_tags(html_content)
                msg = EmailMultiAlternatives(subject, text_content, to=[email])
                msg.attach_alternative(html_content, "text/html")
                msg.send()
        except CondominiumProfile.DoesNotExist:
            pass


def add_manager_notification(condominium, message, request=None, url=None):

    try:
        title = 'Notificação de ' + condominium.condominium_name

        notification = Notification()
        notification.condominium = condominium
        notification.receiver = condominium
        notification.message = message
        notification.title = title
        notification.url = url
        notification.save()

        if request:
            subject = 'Notificação de ' + condominium.condominium_name
            data = add_signature_to_data(request)
            data['message'] = message
            data['domain'] = get_current_site(request).domain
            html_content = render_to_string(
                'info/condominium/reservation/notification_message.html',
                data
            )

            text_content = strip_tags(html_content)
            msg = EmailMultiAlternatives(subject, text_content, to=[condominium.email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()

        for func in condominium.get_employees():
            if func.user_permissions.filter(codename="change_visitant").exists():
                notification_func = Notification()
                notification_func.condominium = condominium
                notification_func.receiver = func
                notification_func.message = message
                notification_func.title = title
                notification_func.url = url
                notification_func.save()

    except CondominiumProfile.DoesNotExist:
        pass


def create_qr_code(code):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(code)
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color="black", back_color="white")
    qr_bytes = BytesIO()
    qr_image.save(qr_bytes, format="PNG")
    file_name = code + ".png"
    return File(qr_bytes, name=file_name)
