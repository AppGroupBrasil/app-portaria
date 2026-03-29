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
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags

from info.forms import AddPedestrianForm, ViewPedestrianForm
from info.info_viwes.condominium_view import _create_code
from info.models import Block, Apartment, Resident, Pedestrian
from info.utils import get_condominium, add_signature_to_data


FIXED_TZ = pytz.timezone("America/Sao_Paulo")


def _attach_pedestrian_photo(pedestrian, profile_pic):
    if not profile_pic:
        return

    image_data = profile_pic.split(',')[1]
    image_bytes = base64.b64decode(image_data)
    image_file = io.BytesIO(image_bytes)
    Image.open(image_file)
    image_file.seek(0)
    pedestrian.photo = InMemoryUploadedFile(
        image_file, None, pedestrian.document + '.jpg', 'image/jpeg', len(image_bytes), None
    )


def _build_pedestrian_from_form(condominium, request, form):
    pedestrian = Pedestrian()
    pedestrian.condominium = condominium
    pedestrian.name = form.cleaned_data['name']
    pedestrian.document = form.cleaned_data['document']
    pedestrian.document_file = form.cleaned_data.get('document_file')
    block = form.cleaned_data['block']
    apartment = form.cleaned_data['apartment']
    pedestrian.destination = f"{block.name}/{apartment.number} {apartment.complement}"
    pedestrian.authorized_by = form.cleaned_data['authorized_by']
    pedestrian.obs = form.cleaned_data['obs']
    pedestrian.protocol = _create_code()
    pedestrian.send_email = request.POST.get("email") == "on"
    pedestrian.send_whatsapp = request.POST.get("whatsapp") == "on"

    _attach_pedestrian_photo(pedestrian, form.cleaned_data.get('webimg'))
    return pedestrian, apartment


def _notify_email(request, title, pedestrian, email):
    subject = f'Notificação de {title}'
    data = add_signature_to_data(request)
    data['name'] = pedestrian.name
    data['obs'] = pedestrian.obs or None
    data['protocol'] = pedestrian.protocol
    html_content = render_to_string(
        'info/condominium/pedestrian/notify_pedestrian.html',
        data
    )
    text_content = strip_tags(html_content)
    msg = EmailMultiAlternatives(subject, text_content, to=[email])
    msg.attach_alternative(html_content, "text/html")
    if pedestrian.photo:
        msg.attach_file(pedestrian.photo.path)
    msg.send()


@login_required(login_url='info:sign-in')
def add_pedrestrian(request):

    condominium = get_condominium(request)
    blocks = Block.objects.filter(condominium=condominium)
    form = AddPedestrianForm(request.POST or None, files=request.FILES or None, blocks=blocks)

    if request.method == "POST":
        if form.is_valid():
            pedestrian, apartment = _build_pedestrian_from_form(condominium, request, form)
            pedestrian.save()

            if pedestrian.send_email:
                residents = Resident.objects.filter(apartment=apartment)

                to_list = []
                for resident in residents:
                    if resident.email:
                        to_list.extend(resident.email.split(';'))

                for email in to_list:
                    threading.Thread(target=_notify_email, args=(request, "Liberação de Pedestre", pedestrian, email)).start()

            if pedestrian.send_whatsapp:
                pass

            messages.success(request, "Pedestre Liberado!")
            return redirect(reverse('info:dashboard'))

    context = {'form': form,
               'whatsapp_not': condominium.whatsapp_notification
               }
    return render(request, "info/condominium/pedestrian/add_pedrestrian.html", context=context)


def pedestrians(request):

    condominium = get_condominium(request)
    pedestrian_list = Pedestrian.objects.filter(condominium=condominium).order_by("-created")

    search_code = request.GET.get('pedestrian_protocol')
    search_name = request.GET.get('pedestrian_name')
    search_document = request.GET.get('pedestrian_document')
    search_date = request.GET.get('pedestrian_date')

    if search_code:
        pedestrian_list = pedestrian_list.filter(protocol__contains=search_code)

    if search_name:
        pedestrian_list = pedestrian_list.filter(name__contains=search_name)

    if search_document:
        pedestrian_list = pedestrian_list.filter(document__contains=search_document)

    if search_date:
        pedestrian_list = pedestrian_list.filter(created__date=search_date)

    pedestrians_counter = pedestrian_list.filter(has_leaved=False).count()

    paginator = Paginator(pedestrian_list, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'pedestrians': page_obj,
               'pedestrians_counter': pedestrians_counter,
               'user': condominium,
               }

    return render(request, "info/condominium/pedestrian/pedestrians.html", context=context)


@login_required(login_url='info:sign-in')
def view_pedestrian(request, id):
    condominium = get_condominium(request)
    pedestrian = get_object_or_404(Pedestrian, pk=id, condominium=condominium)

    form = ViewPedestrianForm(instance=pedestrian)

    context = {'form': form,
               'pedestrian': pedestrian,
               }

    if pedestrian.photo:
        context['img'] = pedestrian.photo

    if pedestrian.document_file:
        context['file'] = pedestrian.document_file

    return render(request, "info/condominium/pedestrian/view_pedestrian.html", context=context)


@login_required(login_url='info:sign-in')
def pedestrian_move(request, id):
    condominium = get_condominium(request)
    pedestrian = get_object_or_404(Pedestrian, pk=id, condominium=condominium)

    if pedestrian.has_leaved:
        pedestrian.has_leaved = False
        pedestrian.created = datetime.now(FIXED_TZ)
        pedestrian.arrived = True
    else:
        pedestrian.has_leaved = True
        pedestrian.leaved_in = datetime.now(FIXED_TZ)
        pedestrian.arrived = False

    pedestrian.save()

    messages.success(request, "Registro realizado!")
    return redirect(reverse('info:pedestrians'))
