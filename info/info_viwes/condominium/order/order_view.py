from io import BytesIO
from datetime import datetime

import pytz
import qrcode
from PIL import Image
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.files import File
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags

from info.forms import OrderNotificationForm, UpdateOrderNotificationForm, ViewOrderNotificationForm
from info.info_viwes.condominium.whatsapp_api.whatsapp_view import send_order_message, send_info_message
from info.info_viwes.condominium_view import _create_code
from info.models import CondominiumProfile, Block, Order, Apartment, Resident, HowTo, Notification, MessagesInformation
from info.utils import get_condominium, add_signature_to_data, add_notification


FIXED_TZ = pytz.timezone("America/Sao_Paulo")


@login_required(login_url='info:sign-in')
def order_notification(request):

    condominium = get_condominium(request)
    blocks = Block.objects.filter(condominium=condominium)

    if request.method == "POST":

        order = Order()
        order.received_by = request.POST.get('received_by')

        order.name = request.POST.get('name')
        if not order.name:
            messages.error(request, "A correspondência precisa de um nome")
            return redirect(reverse('info:notify-order'))

        order.description = request.POST.get('description') or ""
        apt = request.POST.get('apartment')

        if not apt:
            messages.error(request, "Um bloco e apartamento precisa ser selecionados")
            return redirect(reverse('info:notify-order'))

        order.apartment = Apartment.objects.get(pk=int(apt))
        order.image = request.FILES.get('image') or None
        order.addressee = request.POST.get('addressee') or ""
        order.code = _create_code()
        #
        # Generate the QR code
        qr = qrcode.QRCode(version=5, box_size=10, border=1)
        qr.add_data(order.code)
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")
        desired_resolution = (640, 640)
        qr_image = qr_image.resize(desired_resolution, Image.Resampling.LANCZOS)
        qr_bytes = BytesIO()
        qr_image.save(qr_bytes, format="JPEG", quality=95)
        file_name = order.code + ".jpg"

        order.qrcode.save(file_name, File(qr_bytes), save=False)

        to_list = []
        addressee = request.POST.get('addressee')
        if not addressee or addressee == "all":
            messages.success(request, "Todos os moradores foram notificados!")
            residents = Resident.objects.filter(apartment=order.apartment)
            for resident in residents:
                if resident.email:
                    to_list.extend(resident.email.split(';'))
            order.addressee = "TODOS"
        else:
            resident = Resident.objects.get(pk=int(addressee))
            adressee_name = resident.name
            order.addressee = adressee_name
            to_list.extend(resident.email.split(';'))

            if condominium.whatsapp_notification:
                try:
                    messages_info = MessagesInformation.objects.get(condominium=condominium)
                except MessagesInformation.DoesNotExist:
                    messages_info = MessagesInformation()
                    messages_info.condominium = condominium
                    messages_info.save()

                if messages_info.allow_charge or messages_info.messages_used <= messages_info.messages_limit:
                    send_order_message(condominium.condominium_name, resident.name, adressee_name, resident.whatsapp,
                                       order.code, order.qrcode.url)
                    messages_info.messages_used = messages_info.messages_used + 1
                    messages_info.save()

        order.save()

        subject = 'Notificação de encomenda recebida'
        data = add_signature_to_data(request)
        data['order_name'] = order.name
        data['description'] = order.description
        data['code'] = order.code
        data['qrcode'] = order.qrcode.url
        html_content = render_to_string(
            'info/condominium/order/notify_order.html',
            data
        )
        text_content = strip_tags(html_content)
        msg = EmailMultiAlternatives(subject, text_content, to=to_list)
        msg.attach_alternative(html_content, "text/html")
        if order.image:
            msg.attach_file(order.image.path)
        msg.attach_file(order.qrcode.path, 'image/png')
        msg.send()

        messages.success(request, "O morador foi notificado no email cadastrado")
        return redirect(reverse('info:dashboard'))

    form = OrderNotificationForm(request.POST or None, files=request.FILES or None, blocks=blocks)
    form.fields['received_by'].initial = condominium.condominium_name
    form.fields['received_by'].widget.attrs['readonly'] = True

    context = {'form': form,
               }
    return render(request, "info/condominium/order/order_notification.html", context=context)


@login_required(login_url='info:sign-in')
def update_order_notification(request, id):
    condominium = get_condominium(request)
    order = get_object_or_404(Order, pk=id, apartment__block__condominium=condominium)

    if request.method == "POST":

        form = UpdateOrderNotificationForm(request.POST)
        if form.is_valid():
            order.delivered_by = form.cleaned_data['delivered_by'] or ""

            if not form.cleaned_data['collected_by']:
                messages.error(request, "Por favor adicione o nome de quem retirou a correspondência")
                return redirect(reverse('info:update-order', args=[int(order.pk)]))

            order.collected_by = form.cleaned_data['collected_by'] or ""
            order.delivered = datetime.now(FIXED_TZ)
            order.save()
            messages.success(request, "Entrega registrada com sucesso!")

            residents = Resident.objects.filter(apartment=order.apartment)
            for resident in residents:
                if condominium.whatsapp_notification:
                    try:
                        messages_info = MessagesInformation.objects.get(condominium=condominium)
                    except MessagesInformation.DoesNotExist:
                        messages_info = MessagesInformation()
                        messages_info.condominium = condominium
                        messages_info.save()

                    if messages_info.allow_charge or messages_info.messages_used <= messages_info.messages_limit:
                        send_info_message(condominium.condominium_name, order.addressee, resident.whatsapp,
                                          f"A encomenda {order.description} foi retirada por {order.collected_by}")
                        messages_info.messages_used = messages_info.messages_used + 1
                        messages_info.save()

                add_notification(condominium, [resident.email],
                                 f"encomenda {order.description} foi retirada por {order.collected_by}",
                                 request, "/my-orders")

            return redirect(reverse('info:dashboard'))

    form = UpdateOrderNotificationForm(instance=order, block=order.apartment.block,
                                       apartment=order.apartment)
    context = {'form': form,
               }
    return render(request, "info/condominium/order/update_order_notification.html", context=context)


@login_required(login_url='info:sign-in')
def orders(request):
    condominium = get_condominium(request)
    orders_list = Order.objects.filter(apartment__block__condominium=condominium).order_by("-created")

    search_code = request.GET.get('order_code')

    if search_code:
        orders_list = orders_list.filter(code__contains=search_code)

    paginator = Paginator(orders_list, 15)  # Show 20 visitants per page
    page_number = request.GET.get('page')  # Get the page number from the request
    page_obj = paginator.get_page(page_number)

    context = {'orders': orders_list,
               'user': condominium,
               'page_obj': page_obj,
               }

    how_to_order_list = HowTo.objects.get(name__exact="Correspondências > Listagem")
    if how_to_order_list.kind == "Texto":
        context['how_to_order_list_text'] = how_to_order_list.value
    else:
        context['how_to_order_list_link'] = how_to_order_list.value
    return render(request, "info/condominium/order/orders.html", context=context)


@login_required(login_url='info:sign-in')
def view_order_notification(request, id):
    condominium = get_condominium(request)
    order = get_object_or_404(Order, pk=id, apartment__block__condominium=condominium)

    form = ViewOrderNotificationForm(instance=order, block=order.apartment.block,
                                     apartment=order.apartment)

    if not form.fields['delivered_by']:
        form.fields['delivered_by'].initial = ""
    if not form.fields['collected_by']:
        form.fields['collected_by'].initial = ""

    form.fields['received'].initial = order.created.astimezone(FIXED_TZ).strftime('%Y-%m-%d %H:%M:%S')
    form.fields['delivered'].widget.attrs['readonly'] = True

    context = {'form': form,
               'id': order.id,
               }

    if order.image:
        context['img'] = order.image

    return render(request, "info/condominium/order/view_order.html", context=context)


@login_required(login_url='info:sign-in')
@permission_required('info.view_order', login_url='info:sign-in')
def my_orders(request):
    user = CondominiumProfile.objects.get(pk=int(request.user.id))

    try:
        resident = Resident.objects.get(name=user.condominium_name, email=user.email)
    except Resident.DoesNotExist:
        messages.error(request,
                       "Morador não encontrado!")
        return redirect('info:dashboard')

    orders = Order.objects.filter(apartment=resident.apartment).order_by("-created")
    paginator = Paginator(orders, 15)  # Show 20 visitants per page
    page_number = request.GET.get('page')  # Get the page number from the request
    page_obj = paginator.get_page(page_number)

    context = {'orders': orders,
               'page_obj': page_obj}

    return render(request, "info/condominium/order/my_orders.html", context=context)
