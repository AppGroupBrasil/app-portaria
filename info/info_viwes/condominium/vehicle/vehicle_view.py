import base64
import io
from datetime import datetime
import threading

import pytz
from PIL import Image
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags

from info.forms import AddVehicleForm, ViewVehicleForm
from info.info_viwes.condominium_view import _create_code
from info.models import Block, Apartment, Resident, Vehicle
from info.utils import get_condominium, add_signature_to_data


FIXED_TZ = pytz.timezone("America/Sao_Paulo")
AUTO_VEHICLE_CHECKOUT_NOTE = "[BAIXADO PELO SISTEMA]"


def _normalize_vehicle_plate(vehicle_plate):
    if not vehicle_plate:
        return ""
    return str(vehicle_plate).replace(' ', '').replace('-', '').upper()


def _append_vehicle_checkout_note(obs):
    current_obs = (obs or "").strip()
    if AUTO_VEHICLE_CHECKOUT_NOTE in current_obs:
        return current_obs
    if not current_obs:
        return AUTO_VEHICLE_CHECKOUT_NOTE

    max_obs_length = 200
    allowed_prefix_length = max_obs_length - len(AUTO_VEHICLE_CHECKOUT_NOTE) - 1
    return f"{current_obs[:allowed_prefix_length].rstrip()} {AUTO_VEHICLE_CHECKOUT_NOTE}"


def _close_active_vehicle_entries(condominium, vehicle_plate, exclude_pk=None):
    if not vehicle_plate:
        return 0

    active_entries = Vehicle.objects.filter(
        condominium=condominium,
        vehicle_plate__iexact=vehicle_plate,
    ).filter(
        Q(has_leaved=False) | Q(arrived=True)
    )

    if exclude_pk:
        active_entries = active_entries.exclude(pk=exclude_pk)

    closed_count = 0
    now = datetime.now(FIXED_TZ)
    for active_vehicle in active_entries:
        active_vehicle.obs = _append_vehicle_checkout_note(active_vehicle.obs)
        active_vehicle.has_leaved = True
        active_vehicle.arrived = False
        active_vehicle.leaved_in = now
        active_vehicle.save(update_fields=['obs', 'has_leaved', 'arrived', 'leaved_in'])
        closed_count += 1

    return closed_count


def _notify_email(request, title, vehicle, email):
    subject = f'Notificação de {title}'
    data = add_signature_to_data(request)
    data['name'] = vehicle.name
    data['obs'] = vehicle.obs or None
    data['protocol'] = vehicle.protocol
    data['vehicle_plate'] = vehicle.vehicle_plate
    data['vehicle'] = vehicle.vehicle
    html_content = render_to_string(
        'info/condominium/vehicle/notify_vehicle.html',
        data
    )
    text_content = strip_tags(html_content)
    msg = EmailMultiAlternatives(subject, text_content, to=[email])
    msg.attach_alternative(html_content, "text/html")
    if vehicle.photo:
        msg.attach_file(vehicle.photo.path)
    msg.send()


def _attach_vehicle_photo(vehicle, profile_pic):
    if not profile_pic:
        return

    image_data = profile_pic.split(',')[1]
    image_bytes = base64.b64decode(image_data)
    image_file = io.BytesIO(image_bytes)
    Image.open(image_file)
    image_file.seek(0)
    vehicle.photo = InMemoryUploadedFile(
        image_file, None, vehicle.document + '.jpg', 'image/jpeg', len(image_bytes), None
    )


def _build_vehicle_from_request(condominium, request):
    vehicle = Vehicle()
    vehicle.condominium = condominium
    vehicle.name = request.POST.get('name')
    vehicle.document = request.POST.get('document')
    vehicle.document_file = request.FILES.get('document_file') or None

    block = Block.objects.get(pk=int(request.POST.get('block')))
    apartment = Apartment.objects.get(pk=int(request.POST.get('apartment')))

    vehicle.destination = f"{block.name}/{apartment.number} {apartment.complement}"
    vehicle.authorized_by = request.POST.get('authorized_by')
    vehicle.obs = request.POST.get('obs')
    vehicle.vehicle = request.POST.get('vehicle')
    vehicle.vehicle_plate = _normalize_vehicle_plate(request.POST.get('vehicle_plate'))
    vehicle.protocol = _create_code()
    vehicle.send_email = request.POST.get("email") == "on"
    vehicle.send_whatsapp = request.POST.get("whatsapp") == "on"

    _attach_vehicle_photo(vehicle, request.POST.get('webimg'))
    return vehicle, apartment


def _build_vehicle_from_form(condominium, request, form):
    vehicle = Vehicle()
    vehicle.condominium = condominium
    vehicle.name = form.cleaned_data['name']
    vehicle.document = form.cleaned_data['document']
    vehicle.document_file = form.cleaned_data.get('document_file')

    block = form.cleaned_data['block']
    apartment = form.cleaned_data['apartment']

    vehicle.destination = f"{block.name}/{apartment.number} {apartment.complement}"
    vehicle.authorized_by = form.cleaned_data['authorized_by']
    vehicle.obs = form.cleaned_data['obs']
    vehicle.vehicle = form.cleaned_data.get('vehicle')
    vehicle.vehicle_plate = _normalize_vehicle_plate(form.cleaned_data.get('vehicle_plate'))
    vehicle.protocol = _create_code()
    vehicle.send_email = request.POST.get("email") == "on"
    vehicle.send_whatsapp = request.POST.get("whatsapp") == "on"

    _attach_vehicle_photo(vehicle, form.cleaned_data.get('webimg'))
    return vehicle, apartment


def _get_vehicle_notification_recipients(apartment):
    to_list = []
    residents = Resident.objects.filter(apartment=apartment)
    for resident in residents:
        if resident.email:
            to_list.extend(resident.email.split(';'))
    return to_list


def _vehicle_success_message(auto_closed_count):
    if auto_closed_count:
        return f"Veículo liberado! {auto_closed_count} registro(s) anterior(es) com a mesma placa foram baixados automaticamente."
    return "Veículo Liberado!"

@login_required(login_url='info:sign-in')
def add_vehicle(request):

    condominium = get_condominium(request)
    blocks = Block.objects.filter(condominium=condominium)
    form = AddVehicleForm(request.POST or None, files=request.FILES or None, blocks=blocks)

    if request.method == "POST":
        if form.is_valid():
            vehicle, apartment = _build_vehicle_from_form(condominium, request, form)

            vehicle.save()

            if vehicle.send_email:
                for email in _get_vehicle_notification_recipients(apartment):
                    threading.Thread(target=_notify_email, args=(request, "Liberação de Veículo", vehicle, email)).start()

            messages.success(request, "Veículo Liberado!")
            return redirect(reverse('info:dashboard'))

    context = {'form': form,
               }
    return render(request, "info/condominium/vehicle/add_vehicle.html", context=context)


def vehicles(request):

    condominium = get_condominium(request)
    vehicle_list = Vehicle.objects.filter(condominium=condominium).order_by("-created")

    search_code = request.GET.get('vehicle_protocol')
    search_name = request.GET.get('vehicle_name')
    search_document = request.GET.get('vehicle_document')
    search_vehicle = request.GET.get('vehicle')
    search_plate = request.GET.get('vehicle_plate')
    search_date = request.GET.get('vehicle_date')

    if search_code:
        vehicle_list = vehicle_list.filter(protocol__contains=search_code)

    if search_name:
        vehicle_list = vehicle_list.filter(name__contains=search_name)

    if search_document:
        vehicle_list = vehicle_list.filter(document__contains=search_document)

    if search_vehicle:
        vehicle_list = vehicle_list.filter(vehicle__contains=search_vehicle)

    if search_plate:
        vehicle_list = vehicle_list.filter(vehicle_plate__icontains=search_plate)

    if search_date:
        vehicle_list = vehicle_list.filter(created__date=search_date)

    vehicles_counter = vehicle_list.filter(has_leaved=False).count()

    paginator = Paginator(vehicle_list, 15)  # Show 20 visitants per page
    page_number = request.GET.get('page')  # Get the page number from the request
    page_obj = paginator.get_page(page_number)

    context = {'vehicles': page_obj,
               'vehicles_counter': vehicles_counter,
               'user': condominium,
               }

    return render(request, "info/condominium/vehicle/vehicles.html", context=context)


@login_required(login_url='info:sign-in')
def view_vehicle(request, id):
    condominium = get_condominium(request)
    vehicle = get_object_or_404(Vehicle, pk=id, condominium=condominium)

    form = ViewVehicleForm(instance=vehicle)

    context = {'form': form,
               'vehicle': vehicle,
               }

    if vehicle.photo:
        context['img'] = vehicle.photo

    if vehicle.document_file:
        context['file'] = vehicle.document_file

    return render(request, "info/condominium/vehicle/view_vehicle.html", context=context)


@login_required(login_url='info:sign-in')
def vehicle_move(request, id):
    condominium = get_condominium(request)
    vehicle = get_object_or_404(Vehicle, pk=id, condominium=condominium)

    if vehicle.has_leaved:
        vehicle.has_leaved = False
        vehicle.created = datetime.now(FIXED_TZ)
        vehicle.arrived = True
    else:
        vehicle.has_leaved = True
        vehicle.leaved_in = datetime.now(FIXED_TZ)
        vehicle.arrived = False

    vehicle.save()

    messages.success(request, "Registro realizado!")
    return redirect(reverse('info:vehicles'))
