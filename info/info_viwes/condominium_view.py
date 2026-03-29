import base64
import hashlib
import io
import json
import mimetypes
import os
import pytz
import time
import threading
from datetime import datetime, date, timedelta
from os import path
import tempfile
from urllib.request import urlopen

import pandas
from PIL import Image
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from tempfile import NamedTemporaryFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.forms import formset_factory
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.utils import timezone
from django.contrib import messages as info_messages

from info.forms import UserEmailForm, ForgottenPasswordForm, \
    UserUpdateForm, CheckinForm, ResidentSentdLinkForm, BlockLinkForm, EmailLinkForm, AddResidentLinkForm, \
    SignatureForm, SendBillsForm, UserResidentUpdateForm, ExcelUploadForm, ReportLogoForm, CondoMaintenanceActivityForm, \
    AddResidentActivityImageForm, AddResidentActivityFileForm
from info.models import CondominiumProfile, UserLocation, HowTo, Block, Apartment, Resident, Message, Signature, Bill, \
    ResidentActivity, UserControl, ReportLogo, ResidentActivityKind, ResidentActivityImage, ResidentActivityFile, \
    Notification
from info.utils import get_user_from_email_verification_token, check_in, get_condominium, send_verification_email, \
    add_signature_to_data, add_notification, user_check_in, create_qr_code
from info.views import EmailVerificationTokenGenerator, _add_resident_permission

FIXED_TZ = pytz.timezone("America/Sao_Paulo")

def edit_profile(request):
    condominio = CondominiumProfile.objects.get(pk=request.user.id)
    form = UserUpdateForm(instance=condominio)
    if request.method == "POST":
        form = UserUpdateForm(request.POST)
        if form.is_valid():

            condominio.condominium_name = form.cleaned_data['condominium_name'] or condominio.condominium_name
            condominio.cnpj = form.cleaned_data['cnpj'] or condominio.cnpj
            condominio.address = form.cleaned_data['address'] or condominio.address
            condominio.liquidator_name = form.cleaned_data['liquidator_name'] or condominio.liquidator_name
            condominio.whatsapp = form.cleaned_data['whatsapp'] or condominio.whatsapp
            condominio.admin_name = form.cleaned_data['admin_name'] or condominio.admin_name
            condominio.site = form.cleaned_data['site'] or condominio.site
            condominio.save()

            messages.success(request, "Cadastro Atualizado!")
            return redirect(reverse('info:dashboard'))

        else:
            print(form.errors)

    context = {'form': form}

    return render(request, "info/condominium/account/edit_profile.html", context=context)


def edit_resident_profile(request):
    condominio = CondominiumProfile.objects.get(pk=request.user.id)
    form = UserResidentUpdateForm(instance=condominio)
    if request.method == "POST":
        form = UserUpdateForm(request.POST)
        if form.is_valid():

            condominio.condominium_name = form.cleaned_data['condominium_name'] or condominio.condominium_name
            condominio.whatsapp = form.cleaned_data['whatsapp'] or condominio.whatsapp
            condominio.save()
            resident_obj = Resident.objects.get(name=condominio.condominium_name, email=condominio.email)
            resident_obj.condominium_name = condominio.condominium_name
            resident_obj.whatsapp = condominio.whatsapp
            resident_obj.save()

            messages.success(request, "Cadastro Atualizado!")
            return redirect(reverse('info:dashboard'))

        else:
            print(form.errors)

    context = {'form': form}

    return render(request, "info/condominium/account/edit_resident_profile.html", context=context)


@login_required(login_url='info:sign-in')
def update_email(request):
    form = UserEmailForm()

    if request.method == "POST":
        form = UserEmailForm(request.POST)

        if form.is_valid():
            try:

                email = request.POST.get("email")
                db_user = CondominiumProfile.objects.get(email=email)
                messages.error(request, "Solicitação não enviada!, novo email já cadastrado por outro usuário")

            except CondominiumProfile.DoesNotExist:
                user = CondominiumProfile.objects.get(pk=request.user.id)

                email_verification_token = EmailVerificationTokenGenerator()
                current_site = get_current_site(request)

                subject = 'Atualização de email na conta Resolvido Info'
                data = add_signature_to_data(request)
                data['domain'] = current_site.domain
                data['uid'] = urlsafe_base64_encode(force_bytes(user.pk))
                data['n_email'] = urlsafe_base64_encode(force_bytes(email))
                data['token'] = email_verification_token.make_token(user)
                body = render_to_string(
                    'info/condominium/account/change_email.html',
                    data
                )
                text_content = strip_tags(body)
                msg = EmailMultiAlternatives(to=[email], subject=subject, body=text_content)
                msg.attach_alternative(body, "text/html")
                msg.send()

                messages.success(request, "Solicitação enviada!, verifique seu email para validar o novo email")
                return redirect(reverse('info:sign-out'))

    context = {'form': form}

    return render(request, "info/condominium/account/new_email.html", context=context)


def email_verification(request, uidb64, token, n_email):
    user = get_user_from_email_verification_token(self=uidb64, token=token)

    if user:
        try:
            new_email = force_str(urlsafe_base64_decode(n_email))
            user.email = new_email
            user.email_verified = True
            user.save()

            messages.success(request, "Email alterado com sucesso!, Acesse sua conta")
        except IntegrityError:

            messages.error(request, "Email não alterado por já está em uso por outro usuário!, Acesse sua conta")
    else:
        messages.error(request, "Token inválido. Email não alterado")

    return redirect('info:sign-in')


@login_required(login_url='info:sign-in')
def update_password(request):
    user = CondominiumProfile.objects.get(pk=request.user.id)
    form = ForgottenPasswordForm()

    if request.method == "POST":
        form = ForgottenPasswordForm(request.POST)
        if form.is_valid():

            password = request.POST.get("new_password1")
            confirmation = request.POST.get("new_password2")

            try:
                if len(password) != 4:
                    form.add_error(None, "A senha deve conter 4 dígitos")
                elif password == confirmation:
                    if user is not None:
                        user.set_password(password)
                        user.save()
                        messages.success(request, "Senha alterada com sucesso!, Acesse sua conta")
                        return redirect('info:sign-out')
                    else:
                        messages.error(request, "Não existe registro do usuário")
                else:
                    messages.error(request, "As senhas não são iguais")
            except ValueError:
                messages.error(request, "As senhas devem conter apenas números")

    context = {'form': form, }

    if user is not None:
        context['codominio'] = user.condominium_name

    return render(request, "info/condominium/account/password_creation.html", context=context)


def _create_code():
    """This function generate 5 character long hash"""
    hash = hashlib.sha1()
    hash.update(str(time.time()).encode('utf-8'))
    return hash.hexdigest()[:4]


@login_required(login_url='info:sign-in')
def locations(request):
    condominium = get_condominium(request)
    locations_list = UserLocation.objects.filter(condominium=condominium).order_by('-created')
    workers_locations_list = UserLocation.objects.filter(condominium__work_for=condominium).order_by('-created')
    if len(workers_locations_list) > 0:
        locations_list = list(locations_list) + list(workers_locations_list)
        locations_list = sorted(locations_list, key=lambda location: location.created, reverse=True)

    context = {'locations': locations_list,
               'user': condominium
               }
    how_to_location = HowTo.objects.get(name__exact="Localizações > Listagem")
    if how_to_location.kind == "Texto":
        context['how_to_location_text'] = how_to_location.value
    else:
        context['how_to_location_link'] = how_to_location.value
    return render(request, "info/condominium/location/locations.html", context=context)


@login_required(login_url='info:sign-in')
def check_in_page(request, page):
    condominium = CondominiumProfile.objects.get(pk=int(request.user.id))
    form = CheckinForm(page=page)

    if request.method == "POST":

        if not request.POST.get("latitude") or not request.POST.get("longitude"):
            messages.error(request, "Permição de localização é necessária para esta funcionalidade!")
            return redirect(reverse('info:dashboard'))
        location = check_in(request, condominium, request.POST.get("latitude"), request.POST.get("longitude"))
        messages.success(request, "Checkin realizado com sucesso!")
        last_dot_index = page.rfind('.')
        if last_dot_index != -1:
            _page = page[:last_dot_index]
            _id = page[last_dot_index + 1:]
            return redirect(reverse('info:' + _page, args=[int(_id)]))
        return redirect(reverse('info:' + page))
    context = {'form': form,
               }
    return render(request, "info/condominium/account/checkin.html", context=context)


@login_required(login_url='info:sign-in')
def user_check_in_page(request):
    condominium = get_condominium(request)
    user = CondominiumProfile.objects.get(pk=int(request.user.id))

    try:
        UserControl.objects.get(condominium=condominium, user=user, check_out=None)
        messages.error(request, "Sessão já iniciada, faça o checkout para iniciar outra!")
        return redirect(reverse('info:dashboard'))
    except UserControl.DoesNotExist:
        pass

    if request.method == "POST":

        if not request.POST.get("latitude") or not request.POST.get("longitude"):
            messages.error(request, "Permição de localização é necessária para esta funcionalidade!")
            return redirect(reverse('info:dashboard'))

        user_check_in(request, condominium, request.POST.get("latitude"), request.POST.get("longitude"))
        messages.success(request, "Sessão iniciada com sucesso!")
        return redirect(reverse('info:dashboard'))
    context = {
    }
    return render(request, "info/condominium/account/checkin.html", context=context)


@login_required(login_url='info:sign-in')
def user_check_out_page(request):
    condominium = get_condominium(request)
    user = CondominiumProfile.objects.get(pk=int(request.user.id))

    try:
        control = UserControl.objects.filter(condominium=condominium, user=user, check_out=None)
        for ct in control:
            ct.check_out = datetime.now(FIXED_TZ)
            ct.save()
        messages.success(request, "Sessão finalizada com sucesso!")
        return redirect(reverse('info:dashboard'))

    except UserControl.DoesNotExist:
        messages.error(request, "Sessão não iniciada, faça o check-in para iniciar uma!")
        return redirect(reverse('info:dashboard'))


@login_required(login_url='info:sign-in')
def confirm_delete(request, previous, next):
    last_dot_index = next.rfind('.')
    _page = next[:last_dot_index]
    _id = next[last_dot_index + 1:]

    current_site = get_current_site(request)

    context = {'previous': previous,
               'domain': current_site.domain,
               'next': _page + "/" + _id,
               }
    return render(request, "info/condominium/remove.html", context=context)


@login_required(login_url='info:sign-in')
def do_delete(request, page):
    last_dot_index = page.rfind('.')
    if last_dot_index != -1:
        _page = page[:last_dot_index]
        _id = page[last_dot_index + 1:]
        return redirect(reverse('info:' + _page, args=[int(_id)]))
    return redirect(reverse('info:' + page))


@login_required(login_url='info:sign-in')
def residents_link(request):
    if request.method == "POST":
        return send_link_to(request, request.POST.get("link"))

    condominium = CondominiumProfile.objects.get(pk=int(request.user.id))
    email_verification_token = EmailVerificationTokenGenerator()
    current_site = get_current_site(request)

    context = {'domain': current_site.domain,
               'uid': urlsafe_base64_encode(force_bytes(condominium.pk)),
               'token': email_verification_token.make_token(condominium),
               }
    # register_link = "http://" + current_site + {% url 'info:verification' uidb64=uid token=token %}
    return render(request, "info/condominium/apartment/resident_registration.html", context=context)


@login_required(login_url='info:sign-in')
def send_link_to(request, link):
    context = {'link': urlsafe_base64_encode(force_bytes(link))}

    return render(request, "info/condominium/apartment/send_link.html", context=context)


@login_required(login_url='info:sign-in')
def send_link_to_resident(request, link):
    condominium = get_condominium(request)
    blocks = Block.objects.filter(condominium=condominium)
    form = ResidentSentdLinkForm(request.POST or None, blocks=blocks)

    if request.method == "POST":
        apartment = Apartment.objects.get(pk=int(request.POST.get('apartment')))
        residents = Resident.objects.filter(apartment=apartment)

        message = Message()
        message.condominium = condominium
        message.block = apartment.block.name
        message.apartment = str(apartment.number) + " " + apartment.complement
        message.kind = "Ao Morador"

        to_list = []
        for resident in residents:
            if resident.email:
                to_list.extend(resident.email.split(';'))

        subject = 'Cadastro de morador no ' + condominium.condominium_name
        html_content = render_to_string(
            'info/condominium/apartment/registration.html',
            {
                'condominium': condominium.condominium_name,
                'message': force_str(urlsafe_base64_decode(link)),
            }
        )

        text_content = strip_tags(html_content)
        msg = EmailMultiAlternatives(subject, text_content, to=to_list)
        msg.attach_alternative(html_content, "text/html")
        message.set_to_list(to_list)
        message.message = force_str(urlsafe_base64_decode(link))
        message.save()

        msg.send()
        info_messages.success(request, "O morador recebeu o link no email cadastrado")
        return redirect(reverse('info:dashboard'))

    context = {'form': form,
               }

    return render(request, "info/condominium/apartment/link_resident.html", context=context)


def bills(request):
    condominium = get_condominium(request)
    bills_list = Bill.objects.filter(condominium=condominium)

    search_sender_name = request.GET.get('sender_name')
    search_receiver_name = request.GET.get('receiver_name')
    search_receiver_email = request.GET.get('receiver_email')

    if search_sender_name:
        bills_list = bills_list.filter(sender__contains=search_sender_name)

    if search_receiver_name:
        bills_list = bills_list.filter(user__condominium_name__contains=search_receiver_name)

    if search_receiver_email:
        bills_list = bills_list.filter(user__email__contains=search_receiver_email)

    bills_objs = []
    for bill in bills_list:
        try:
            resident = Resident.objects.get(email=bill.user.email, apartment__block__condominium=condominium,
                                            name=bill.user.condominium_name)
            apt = str(resident.apartment.number)
            cmpl = resident.apartment.complement
            if cmpl:
                address = resident.apartment.block.name + " / " + apt + " " + cmpl
            else:
                address = resident.apartment.block.name + " / " + apt
            bills_obj = {
                'user': bill.user,
                'file': bill.file,
                'sender': bill.sender,
                'created': bill.created.astimezone(FIXED_TZ),
                'address': address,
            }
            bills_objs.append(bills_obj)
        except Resident.DoesNotExist:
            pass

    context = {'bills': bills_objs,
               'user': condominium}

    return render(request, "info/condominium/finance/bills.html", context=context)


@login_required(login_url='info:sign-in')
def send_bills(request):
    condominium = get_condominium(request)
    sender = CondominiumProfile.objects.get(pk=int(request.user.id))
    form = SendBillsForm(request.POST or None, files=request.FILES or None)

    context = {'form': form,
               }

    if request.method == "POST":
        if form.is_valid():
            files = form.cleaned_data["files"]
            for file in files:
                file_name = file.name
                last_dot_index = file_name.rfind('.')
                if last_dot_index != -1:
                    address = file_name[:last_dot_index]
                else:
                    address = file_name

                address = address.split('_')

                block = address[0].replace("-", " ")
                apt = address[1].replace("-", " ")
                complement = ""

                first_space_index = apt.find(' ')
                if first_space_index:
                    apt_aux = apt[:first_space_index]
                    complement = apt[first_space_index + 1:]
                    apt = apt_aux

                try:
                    residents = Resident.objects.filter(apartment__block__condominium=condominium,
                                                        apartment__block__name__iexact=block,
                                                        apartment__complement__iexact=complement,
                                                        apartment__number=int(apt))
                    if not len(residents):
                        message = "O morador do " + block + " / " + apt + " " + complement + " não foi encontrado."
                        info_messages.error(request, message)
                        return render(request, "info/condominium/apartment/send_bills.html", context=context)
                    for resident in residents:
                        try:
                            user = CondominiumProfile.objects.get(email=resident.email, resident_in=condominium,
                                                                  condominium_name=resident.name)

                            bill = Bill()
                            bill.user = user
                            bill.condominium = condominium
                            bill.file = file
                            bill.sender = sender.condominium_name
                            bill.save()

                            send_bill_to_email(request, resident, file)
                            add_notification(condominium, [resident.email],
                                             "Novo boleto recebido. Verifique sua caixa de entrada, lixo eletrônico ou aplicação.",
                                             None, "/my-bills")

                        except CondominiumProfile.DoesNotExist:
                            send_bill_to_email(request, resident, file)

                except Resident.DoesNotExist:
                    message = "O morador do " + block + " / " + apt + " " + complement + " não foi encontrado."
                    info_messages.error(request, message)
                    return render(request, "info/condominium/apartment/send_bills.html", context=context)

            message = "Arquivos enviado ao contato/aplicação do morador."
            info_messages.success(request, message)

    return render(request, "info/condominium/apartment/send_bills.html", context=context)


def send_bill_to_email(request, resident, file):
    to_list = []
    if resident.email:
        to_list.extend(resident.email.split(';'))

    condominium = get_condominium(request)
    subject = 'Novo boleto enviado por ' + condominium.condominium_name

    data = add_signature_to_data(request)
    data[
        'message'] = "Um novo BOLETO foi enviado para você. Faça o donwload do arquivo anexo ou através da aplicação AppSindico"
    html_content = render_to_string(
        'info/condominium/messages/message.html',
        data
    )

    text_content = strip_tags(html_content)
    msg = EmailMultiAlternatives(subject, text_content, to=to_list)
    msg.attach_alternative(html_content, "text/html")

    msg.attach(file.name, file.file.getvalue(), mimetypes.guess_type(file.name)[0])

    msg.send()


@login_required(login_url='info:sign-in')
@permission_required('info.my_bills', login_url='info:sign-in')
def my_bills(request):
    condominium = get_condominium(request)
    user = CondominiumProfile.objects.get(pk=int(request.user.id))

    bills = Bill.objects.filter(condominium=condominium, user=user).order_by("-created")

    context = {'bills': bills}

    return render(request, "info/condominium/apartment/my_bills.html", context=context)


@login_required(login_url='info:sign-in')
def send_link_to_block(request, link):
    condominium = get_condominium(request)
    blocks = Block.objects.filter(condominium=condominium)
    form = BlockLinkForm(request.POST or None, blocks=blocks)

    if request.method == "POST":
        block = Block.objects.get(pk=int(request.POST.get('block')))

        message = Message()
        message.condominium = condominium
        message.block = block.name
        message.apartment = "Todos"
        message.kind = "Ao Bloco"

        residents = Resident.objects.filter(apartment__block=block)

        to_list = []
        for resident in residents:
            if resident.email:
                to_list.extend(resident.email.split(';'))

        subject = 'Cadastro de morador no ' + condominium.condominium_name
        html_content = render_to_string(
            'info/condominium/apartment/registration.html',
            {
                'condominium': condominium.condominium_name,
                'message': force_str(urlsafe_base64_decode(link)),
            }
        )

        text_content = strip_tags(html_content)
        msg = EmailMultiAlternatives(subject, text_content, to=to_list)
        msg.attach_alternative(html_content, "text/html")
        message.set_to_list(to_list)
        message.message = force_str(urlsafe_base64_decode(link))
        message.save()

        msg.send()
        info_messages.success(request, "Os moradores do bloco receberam o link no email cadastrado")
        return redirect(reverse('info:dashboard'))

    context = {'form': form,
               }

    return render(request, "info/condominium/apartment/link_block.html", context=context)


@login_required(login_url='info:sign-in')
def send_link_to_all(request, link):
    condominium = get_condominium(request)

    message = Message()
    message.condominium = condominium
    message.block = "Todos"
    message.apartment = "Todos"
    message.kind = "Ao Condomínio"

    residents = Resident.objects.filter(apartment__block__condominium=condominium)

    to_list = []
    for resident in residents:
        if resident.email:
            to_list.extend(resident.email.split(';'))

    subject = 'Cadastro de morador no ' + condominium.condominium_name
    html_content = render_to_string(
        'info/condominium/apartment/registration.html',
        {
            'condominium': condominium.condominium_name,
            'message': force_str(urlsafe_base64_decode(link)),
        }
    )

    text_content = strip_tags(html_content)
    msg = EmailMultiAlternatives(subject, text_content, to=to_list)
    msg.attach_alternative(html_content, "text/html")
    message.set_to_list(to_list)
    message.message = force_str(urlsafe_base64_decode(link))
    message.save()

    msg.send()
    info_messages.success(request, "Todos os moradores do condomínio receberam o link no email cadastrado")
    return redirect(reverse('info:dashboard'))


@login_required(login_url='info:sign-in')
def send_link_to_email(request, link):
    condominium = get_condominium(request)
    form = EmailLinkForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():

            email = form.cleaned_data['email']

            subject = 'Cadastro de morador no ' + condominium.condominium_name
            user = CondominiumProfile.objects.get(pk=request.user.id)
            try:

                signature = Signature.objects.get(condominium=user)
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

            current_site = get_current_site(request)
            html_content = render_to_string(
                'info/condominium/apartment/registration.html',
                {
                    'condominium': condominium.condominium_name,
                    'message': force_str(urlsafe_base64_decode(link)),
                    'signature': signature,
                    'email': signature_email,
                    'name': name,
                    'whatsapp': whatsapp,
                    'signature_image': signature_image,
                    'current_site': current_site,
                }
            )

            text_content = strip_tags(html_content)
            msg = EmailMultiAlternatives(subject, text_content, to=[email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            info_messages.success(request, "O link foi enviado no email inserido")
            return redirect(reverse('info:dashboard'))

    context = {'form': form,
               }

    return render(request, "info/condominium/apartment/link_email.html", context=context)


def add_resident_by_link(request, uidb64, token):
    condominium = get_user_from_email_verification_token(self=uidb64, token=token)
    blocks = Block.objects.filter(condominium=condominium)

    form = AddResidentLinkForm(request.POST or None, request.FILES or None, blocks=blocks)

    if request.method == "POST":
        print(request.POST)
        print(request.FILES)
        # if form.is_valid():
        # apartment = Con.objects.get(pk=int(request.POST.get('apartment')))
        try:
            resident = CondominiumProfile()
            resident.condominium_name = request.POST.get('resident_name')
            resident.email = str(request.POST.get('email')).lower()
            resident.resident_in = condominium
            resident.plan_expiration = condominium.plan_expiration
            resident.whatsapp = request.POST.get('whatsapp') or ""

            profile_pic = request.POST.get(
                'webimg')  # src is the name of input attribute in your html file, this src value is set in javascript code
            if profile_pic:
                image_data = profile_pic.split(',')[1]  # Remove the data URI prefix
                image_bytes = base64.b64decode(image_data)
                image_file = io.BytesIO(image_bytes)
                Image.open(image_file)
                image_file.seek(0)
                resident.profile_pic = InMemoryUploadedFile(
                    image_file, None, resident.condominium_name + '.jpg', 'image/jpeg', len(image_bytes), None)

            if request.POST.get("default_pass") is not None and request.POST.get("default_pass") == "on":
                password = request.POST.get("new_password1")
                confirmation = request.POST.get("new_password2")

                try:
                    if len(password) != 4:
                        messages.error("A senha deve conter 4 dígitos")
                        error = True
                    elif int(password) == int(confirmation):

                        resident.set_password(password)
                        resident.is_active = True
                        resident.email_verified = True
                        resident.added_by_link = False
                        resident.use_tabs = condominium.use_tabs

                    else:
                        messages.error(request, "As senhas não são iguais")
                        error = True
                except ValueError:
                    messages.error(request, "As senhas devem conter apenas números")
                    error = True
            else:
                resident.added_by_link = True

            resident.save()

            _add_resident_permission(resident)

            apartment = Apartment.objects.get(pk=int(request.POST.get('apartment')))

            try:
                apt_resident = Resident.objects.get(email=resident.email, apartment=apartment)
                apt_resident.name = resident.condominium_name
                apt_resident.kind = request.POST.get('kind')
                apt_resident.apartment = apartment
                apt_resident.whatsapp = request.POST.get('whatsapp') or ""
                apt_resident.save()
            except Resident.DoesNotExist:
                apt_resident = Resident()
                apt_resident.name = resident.condominium_name
                apt_resident.email = resident.email
                apt_resident.kind = request.POST.get('kind')
                apt_resident.apartment = apartment
                apt_resident.whatsapp = request.POST.get('whatsapp') or ""
                apt_resident.save()

            if resident.added_by_link:
                send_verification_email(request, resident)
                messages.success(request, "Morador Cadastrado! Cadastre uma senha clicando no email recebido.")
            else:
                messages.success(request, "Morador Cadastrado! Utilize a senha cadastrada para realizar o login.")

            return redirect(reverse('info:dashboard'))
        except IntegrityError:

            messages.error(request, "O email do morador já está em uso por outro usuário! Utilize outro email")

    context = {'form': form,
               }
    return render(request, "info/condominium/account/add_resident.html", context=context)


@login_required(login_url='info:sign-in')
def add_signature(request):
    condominium = CondominiumProfile.objects.get(pk=int(request.user.id))

    if request.method == "POST":
        form = SignatureForm(request.POST, files=request.FILES)
        if form.is_valid():
            try:
                signature = Signature.objects.get(condominium=condominium)
            except Signature.DoesNotExist:
                signature = Signature()
                signature.condominium = condominium

            signature.name = form.cleaned_data['name'] or ""
            signature.email = form.cleaned_data['email'] or ""
            signature.whatsapp = form.cleaned_data['whatsapp'] or ""

            if form.cleaned_data['image']:
                signature.image = form.cleaned_data['image']
            signature.save()

        messages.success(request, "Assinatura salva!")
        return redirect(reverse('info:dashboard'))

    form = SignatureForm(email=condominium.email, whatsapp=condominium.whatsapp, name=condominium.condominium_name)
    context = {'form': form, }
    return render(request, "info/condominium/account/add_signature.html", context=context)


@login_required(login_url='info:sign-in')
def add_report_logo(request):
    condominium = CondominiumProfile.objects.get(pk=int(request.user.id))

    if request.method == "POST":
        form = ReportLogoForm(request.POST, files=request.FILES)
        if form.is_valid():
            try:
                logo = ReportLogo.objects.get(condominium=condominium)
            except ReportLogo.DoesNotExist:
                logo = ReportLogo()
                logo.condominium = condominium

            if form.cleaned_data['image']:
                logo.image = form.cleaned_data['image']
                logo.save()

        messages.success(request, "Logo de relatórios salvo!")
        return redirect(reverse('info:dashboard'))

    form = ReportLogoForm()
    context = {'form': form, }
    return render(request, "info/condominium/account/add_report_logo.html", context=context)


def resident_activities(request):
    condominium = get_condominium(request)
    activities = ResidentActivity.objects.filter(condominium=condominium).order_by("-created")

    search_protocol = request.GET.get('protocol')
    search_title = request.GET.get('title')
    search_block = request.GET.get('block')
    # search_apartment = request.GET.get('apartment')
    search_resident = request.GET.get('resident')
    search_status = request.GET.get('status_filter')

    if search_protocol:
        activities = activities.filter(protocol__contains=search_protocol)

    if search_title:
        activities = activities.filter(title__contains=search_title)

    if search_resident:
        activities = activities.filter(resident__contains=search_resident)

    if search_block:
        activities = activities.filter(apartment__block__name__contains=search_block)

    # if search_apartment:
    #     activities = activities.filter(apartment__ =search_apartment)

    if search_status:
        activities = activities.filter(status=search_status)

    context = {'activities': activities}

    return render(request, "info/condominium/apartment/resident_activities.html", context=context)


def deactivate_expired_users(request):
    utc_now = timezone.now()
    current_date = utc_now.astimezone(FIXED_TZ).date()
    expired_users = CondominiumProfile.objects.filter(plan_expiration__lt=current_date, is_active=True, is_staff=False)
    expired_users.update(is_active=False)
    info_messages.success(request, "Usuários Verificados!")
    return redirect(reverse('info:dashboard'))


def _handle_uploaded_file(file):
    temp_file = NamedTemporaryFile(delete=False)
    file_path = temp_file.name
    with open(file_path, 'wb') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    return file_path


def _process_excel_data(request, file_path, email):
    # Process the Excel file using pandas

    try:
        df = pandas.read_excel(file_path)
    except ValueError:
        try:
            df = pandas.read_csv(file_path)
        except ValueError:
            messages.error(request, "Formato de arquivo não reconhecido!")
            return

    df.dropna(axis=0, how='all', inplace=True)
    # Iterate through the rows of the DataFrame and create/save models
    # data = str(df.iloc[12][0])
    # print("## ",data, " ##")

    for index, row in df.iloc[:].iterrows():
        try:
            if index > 0:
                condominio_name = str(row[0])

                try:
                    condominium = CondominiumProfile.objects.get(condominium_name=condominio_name)
                    block_name = str(row[1])
                    try:
                        block = Block.objects.get(condominium=condominium, name=block_name)
                    except Block.DoesNotExist:
                        block = Block()
                        block.name = block_name
                        block.condominium = condominium
                        block.save()

                    apt_number = int(row[2])
                    apt_complement = str(row[3]) if str(row[3]) != "nan" else ""

                    try:
                        apartment = Apartment.objects.get(block=block, number=apt_number, complement=apt_complement)
                    except Apartment.DoesNotExist:
                        apartment = Apartment()
                        apartment.block = block
                        apartment.number = apt_number
                        apartment.complement = apt_complement
                        apartment.save()

                    resident = Resident()
                    resident.apartment = apartment
                    resident.name = str(row[4])
                    email_from_file = str(row[5]) if str(row[5]) != "nan" else ""
                    if ";" in email_from_file:
                        email_from_file = email_from_file[0:email_from_file.find(";")]
                    resident.email = email_from_file
                    resident.kind = str(row[6]) if str(row[6]) != "nan" else ""
                    whatsapp_from_file = str(row[7]) if str(row[7]) != "nan" else ""
                    if whatsapp_from_file:
                        whatsapp_from_file = whatsapp_from_file.strip()
                    if ";" in whatsapp_from_file:
                        whatsapp_from_file = whatsapp_from_file[0:whatsapp_from_file.find(";")]
                    whatsapp_from_file = whatsapp_from_file.replace("+55 ", "")
                    whatsapp_from_file = whatsapp_from_file.replace("+55", "")
                    resident.whatsapp = whatsapp_from_file

                    try:
                        resident_db = Resident.objects.get(apartment=apartment, email=resident.email,
                                                           name__iexact=resident.name)
                        resident_db.delete()
                    except Resident.DoesNotExist:
                        resident.save()

                    try:
                        old_user = CondominiumProfile.objects.get(email=resident.email)
                        old_user.delete()
                        CondominiumProfile.objects.get(email=resident.email)
                    except CondominiumProfile.DoesNotExist:
                        try:

                            resident_user = CondominiumProfile()
                            resident_user.condominium_name = resident.name
                            resident_user.email = resident.email.lower()
                            resident_user.resident_in = condominium
                            resident_user.plan_expiration = condominium.plan_expiration
                            resident_user.whatsapp = resident.whatsapp
                            error = False
                            try:
                                password = str(row[8])

                                if len(password) != 4:
                                    messages.error(request, "A senha deve conter 4 dígitos")
                                    error = True

                                else:
                                    int(password)
                                    resident_user.set_password(password)

                            except ValueError:
                                messages.error(request, "As senhas devem conter apenas números")
                                error = True

                            if error:
                                resident.delete()
                            else:

                                resident_user.is_active = True
                                resident_user.email_verified = True
                                resident_user.added_by_link = False
                                resident_user.use_tabs = condominium.use_tabs
                                resident_user.save()

                                _add_resident_permission(resident_user)

                        except IntegrityError:

                            messages.error(request,
                                           "O email " + resident.email + " do morador já está em uso por outro usuário! Utilize outro email")
                            resident.delete()

                except CondominiumProfile.DoesNotExist:
                    messages.error(request,
                                   "O nome do condomínio não foi encontrado! Cadatre os moradores manualmente ouo entre em contato com o suporte.")

        except IndexError:
            print("Column index out of range for row:", index)

    os.remove(file_path)

    messages.success(request, "Cadastro realizado!")


@login_required(login_url='info:sign-in')
def add_resident_from_file(request):
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            file_name = excel_file.name
            last_dot_index = file_name.rfind('.')
            if last_dot_index != -1:
                email = file_name[:last_dot_index]
            else:
                email = file_name

            file_path = _handle_uploaded_file(excel_file)

            # threading.Thread(target=_process_excel_data, args=(request, file_path, email)).start()
            _process_excel_data(request, file_path, email)

            return redirect(reverse('info:residents'))
    else:
        form = ExcelUploadForm()
    return render(request, 'info/condominium/apartment/add_from_file.html', {'form': form})


def add_condominium_maintenance_activity(request):
    condominium = get_condominium(request)
    user = CondominiumProfile.objects.get(pk=int(request.user.id))

    try:
        activity_kind = ResidentActivityKind.objects.get(condominium=condominium, name__exact="MANUTENÇÃO")

    except ResidentActivityKind.DoesNotExist:
        test_kind = ResidentActivityKind()
        test_kind.condominium = condominium
        test_kind.name = "MANUTENÇÃO"
        test_kind.save()

    workers = CondominiumProfile.objects.filter(work_for=condominium)
    residents = CondominiumProfile.objects.filter(resident_in=condominium)
    form = CondoMaintenanceActivityForm(
        request.POST or None, workers=workers, residents=residents)

    ActivityImageFormset = formset_factory(AddResidentActivityImageForm, extra=0)
    images_formset = ActivityImageFormset(request.POST or None, files=request.FILES or None,
                                          prefix="imagens")
    ActivityFileFormset = formset_factory(AddResidentActivityFileForm, extra=0)
    files_formset = ActivityFileFormset(request.POST or None, files=request.FILES or None,
                                        prefix="files")

    if request.method == "POST":
        if all([form.is_valid(), images_formset.is_valid(), files_formset.is_valid()]):
            activity = ResidentActivity()
            activity.condominium = condominium
            activity.kind = "MANUTENÇÃO"
            activity.protocol = _create_code()
            activity.title = form.cleaned_data['title']
            activity.description = form.cleaned_data['description']
            activity.resident = user.condominium_name
            activity.status = "EM EXECUÇÃO"
            activity.qrcode = create_qr_code(activity.protocol)

            if user.work_for:
                activity.profile = "FUNCIONÁRIO"
            elif user.profile == "main":
                activity.profile = "SÍNDICO"
            else:
                activity.profile = user.profile.upper()

            to_list = []
            worker = form.cleaned_data['worker_responsible']
            if worker:
                activity.worker_responsible = worker
                to_list.append(worker.email)

            resident = form.cleaned_data['resident_responsible']
            if resident:
                activity.resident_responsible = resident
                to_list.append(resident.email)

            activity.save()

            for image_form in images_formset:
                if image_form.has_changed():
                    image_model = ResidentActivityImage()
                    image_model.resident_activity = activity
                    image_model.image = image_form.cleaned_data["image"]
                    image_model.save()

            for file_form in files_formset:
                if file_form.has_changed():
                    file_model = ResidentActivityFile()
                    file_model.resident_activity = activity
                    file_model.file = file_form.cleaned_data["file"]
                    file_model.save()

            add_notification(condominium, to_list,
                             "NOVA SOLICITAÇÃO RECEBIDA. " + activity.title.upper() +
                             ". Acesse através do menu Atividades.")

            messages.success(request, "Solicitação feita, o responsável será notificado, acompanhe o status pela sua"
                                      "aplicação!")


            return redirect(reverse('info:resident-activities'))
        else:
            print("ERRORS: ", form.errors)

    context = {'form': form,
               'images_formset': images_formset,
               'files_formset': files_formset,
               }
    how_to_image = HowTo.objects.get(name__exact="Informativo > Imagens")
    if how_to_image.kind == "Texto":
        context['how_to_image_text'] = how_to_image.value
    else:
        context['how_to_image_link'] = how_to_image.value
    how_to_file = HowTo.objects.get(name__exact="Informativo > Arquivos")
    if how_to_file.kind == "Texto":
        context['how_to_file_text'] = how_to_file.value
    else:
        context['how_to_file_link'] = how_to_file.value

    return render(request, "info/condominium/apartment/condominium_maintenance_activity.html", context=context)


def add_condominium_inspect_activity(request):
    condominium = get_condominium(request)
    user = CondominiumProfile.objects.get(pk=int(request.user.id))

    try:
        activity_kind = ResidentActivityKind.objects.get(condominium=condominium, name__exact="VISTORIA")

    except ResidentActivityKind.DoesNotExist:
        test_kind = ResidentActivityKind()
        test_kind.condominium = condominium
        test_kind.name = "VISTORIA"
        test_kind.save()

    workers = CondominiumProfile.objects.filter(work_for=condominium)
    residents = CondominiumProfile.objects.filter(resident_in=condominium)
    form = CondoMaintenanceActivityForm(
        request.POST or None, workers=workers, residents=residents)

    ActivityImageFormset = formset_factory(AddResidentActivityImageForm, extra=0)
    images_formset = ActivityImageFormset(request.POST or None, files=request.FILES or None,
                                          prefix="imagens")
    ActivityFileFormset = formset_factory(AddResidentActivityFileForm, extra=0)
    files_formset = ActivityFileFormset(request.POST or None, files=request.FILES or None,
                                        prefix="files")

    if request.method == "POST":
        if all([form.is_valid(), images_formset.is_valid(), files_formset.is_valid()]):
            activity = ResidentActivity()
            activity.condominium = condominium
            activity.kind = "VISTORIA"
            activity.protocol = _create_code()
            activity.title = form.cleaned_data['title']
            activity.description = form.cleaned_data['description']
            activity.resident = user.condominium_name
            activity.status = "EM EXECUÇÃO"
            activity.qrcode = create_qr_code(activity.protocol)

            if user.work_for:
                activity.profile = "FUNCIONÁRIO"
            elif user.profile == "main":
                activity.profile = "SÍNDICO"
            else:
                activity.profile = user.profile.upper()

            to_list = []
            worker = form.cleaned_data['worker_responsible']
            if worker:
                activity.worker_responsible = worker
                to_list.append(worker.email)

            resident = form.cleaned_data['resident_responsible']
            if resident:
                activity.resident_responsible = resident
                to_list.append(resident.email)

            activity.save()

            for image_form in images_formset:
                if image_form.has_changed():
                    image_model = ResidentActivityImage()
                    image_model.resident_activity = activity
                    image_model.image = image_form.cleaned_data["image"]
                    image_model.save()

            for file_form in files_formset:
                if file_form.has_changed():
                    file_model = ResidentActivityFile()
                    file_model.resident_activity = activity
                    file_model.file = file_form.cleaned_data["file"]
                    file_model.save()

            add_notification(condominium, to_list,
                             "NOVA SOLICITAÇÃO RECEBIDA. " + activity.title.upper() +
                             ". Acesse através do menu Atividades.")

            messages.success(request, "Solicitação feita, o responsável será notificado, acompanhe o status pela sua"
                                      "aplicação!")


            return redirect(reverse('info:resident-activities'))
        else:
            print("ERRORS: ", form.errors)

    context = {'form': form,
               'images_formset': images_formset,
               'files_formset': files_formset,
               }
    how_to_image = HowTo.objects.get(name__exact="Informativo > Imagens")
    if how_to_image.kind == "Texto":
        context['how_to_image_text'] = how_to_image.value
    else:
        context['how_to_image_link'] = how_to_image.value
    how_to_file = HowTo.objects.get(name__exact="Informativo > Arquivos")
    if how_to_file.kind == "Texto":
        context['how_to_file_text'] = how_to_file.value
    else:
        context['how_to_file_link'] = how_to_file.value

    return render(request, "info/condominium/apartment/condominium_inspect_activity.html", context=context)


def add_condominium_occurrence_activity(request):
    condominium = get_condominium(request)
    user = CondominiumProfile.objects.get(pk=int(request.user.id))

    try:
        activity_kind = ResidentActivityKind.objects.get(condominium=condominium, name__exact="OCORRÊNCIA")

    except ResidentActivityKind.DoesNotExist:
        test_kind = ResidentActivityKind()
        test_kind.condominium = condominium
        test_kind.name = "OCORRÊNCIA"
        test_kind.save()

    workers = CondominiumProfile.objects.filter(work_for=condominium)
    residents = CondominiumProfile.objects.filter(resident_in=condominium)
    form = CondoMaintenanceActivityForm(
        request.POST or None, workers=workers, residents=residents)

    ActivityImageFormset = formset_factory(AddResidentActivityImageForm, extra=0)
    images_formset = ActivityImageFormset(request.POST or None, files=request.FILES or None,
                                          prefix="imagens")
    ActivityFileFormset = formset_factory(AddResidentActivityFileForm, extra=0)
    files_formset = ActivityFileFormset(request.POST or None, files=request.FILES or None,
                                        prefix="files")

    if request.method == "POST":
        if all([form.is_valid(), images_formset.is_valid(), files_formset.is_valid()]):
            activity = ResidentActivity()
            activity.condominium = condominium
            activity.kind = "OCORRÊNCIA"
            activity.protocol = _create_code()
            activity.title = form.cleaned_data['title']
            activity.description = form.cleaned_data['description']
            activity.resident = user.condominium_name
            activity.status = "EM EXECUÇÃO"
            activity.qrcode = create_qr_code(activity.protocol)

            if user.work_for:
                activity.profile = "FUNCIONÁRIO"
            elif user.profile == "main":
                activity.profile = "SÍNDICO"
            else:
                activity.profile = user.profile.upper()

            to_list = []
            worker = form.cleaned_data['worker_responsible']
            if worker:
                activity.worker_responsible = worker
                to_list.append(worker.email)

            resident = form.cleaned_data['resident_responsible']
            if resident:
                activity.resident_responsible = resident
                to_list.append(resident.email)

            activity.save()

            for image_form in images_formset:
                if image_form.has_changed():
                    image_model = ResidentActivityImage()
                    image_model.resident_activity = activity
                    image_model.image = image_form.cleaned_data["image"]
                    image_model.save()

            for file_form in files_formset:
                if file_form.has_changed():
                    file_model = ResidentActivityFile()
                    file_model.resident_activity = activity
                    file_model.file = file_form.cleaned_data["file"]
                    file_model.save()

            add_notification(condominium, to_list,
                             "NOVA OCORRÊNCIA RECEBIDA. " + activity.title.upper() +
                             ". Acesse através do menu Atividades.")

            messages.success(request, "Solicitação feita, o responsável será notificado, acompanhe o status pela sua"
                                      "aplicação!")


            return redirect(reverse('info:resident-activities'))
        else:
            print("ERRORS: ", form.errors)

    context = {'form': form,
               'images_formset': images_formset,
               'files_formset': files_formset,
               }
    how_to_image = HowTo.objects.get(name__exact="Informativo > Imagens")
    if how_to_image.kind == "Texto":
        context['how_to_image_text'] = how_to_image.value
    else:
        context['how_to_image_link'] = how_to_image.value
    how_to_file = HowTo.objects.get(name__exact="Informativo > Arquivos")
    if how_to_file.kind == "Texto":
        context['how_to_file_text'] = how_to_file.value
    else:
        context['how_to_file_link'] = how_to_file.value

    return render(request, "info/condominium/apartment/condominium_occurrence_activity.html", context=context)


def well_known_assets(request):
    data = [
        {
            "relation": [
                "delegate_permission/common.handle_all_urls",
                "delegate_permission/common.get_login_creds"
            ],
            "target": {
                "namespace": "android_app",
                "package_name": "com.appportaria",
                "sha256_cert_fingerprints": [
                    "B8:79:E0:F8:AC:60:87:E4:58:65:0E:9B:03:A3:6C:5F:2A:1E:8D:35:21:68:CC:51:EC:86:E2:A2:7D:B8:76:F4"
                ]
            }
        },
        {
            "relation": [
                "delegate_permission/common.handle_all_urls"
            ],
            "target": {
                "namespace": "android_app",
                "package_name": "com.appportaria.twa",
                "sha256_cert_fingerprints": [
                    "8B:24:B0:24:B8:65:9C:A7:C3:22:58:B7:11:7C:50:A4:AB:14:40:3D:F3:1D:B4:87:C9:07:A0:2E:3C:EE:32:87"
                ]
            }
        },
        {
            "relation": [
                "delegate_permission/common.handle_all_urls"
            ],
            "target": {
                "namespace": "twa.com.appportaria.twa",
                "package_name": "twa.com.appportaria.twa",
                "sha256_cert_fingerprints": [
                    "8B:24:B0:24:B8:65:9C:A7:C3:22:58:B7:11:7C:50:A4:AB:14:40:3D:F3:1D:B4:87:C9:07:A0:2E:3C:EE:32:87"
                ]
            }
        }
    ]
    json_string = json.dumps(data)
    return JsonResponse(data=data,safe=False)
    # return render(request, 'info/assetlinks.json')


@login_required(login_url='info:sign-in')
def my_notifications(request):
    condominium = CondominiumProfile.objects.get(pk=int(request.user.id))
    notifications = Notification.objects.filter(receiver=condominium).order_by('-created')

    paginator = Paginator(notifications, 20)  # Show 20 visitants per page
    page_number = request.GET.get('page')  # Get the page number from the request
    page_obj = paginator.get_page(page_number)
    context = {'notifications': notifications,
               'user': condominium,
               'page_obj': page_obj
               }

    return render(request, "info/condominium/notification/notifications.html", context=context)


def delete_apt(request):
    condominium = get_condominium(request)
    apartments = Apartment.objects.filter(complement="0")

    for apartment in apartments:
        apartment.delete()

    return redirect(reverse('info:dashboard'))