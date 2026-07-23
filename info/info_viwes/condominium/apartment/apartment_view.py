import base64
import datetime
import hashlib
import io
import time

import pytz
from PIL import Image
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Count, Q, F, Max
from django.forms import modelformset_factory
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags

from info.forms import AddApartmentForm, AddedApartmentForm, AddResidentForm, UpdateResidentForm, AddVisitantForm, \
    RegisterVisitant, AddBlockForm, ViewUserForm, ResidentActivityForm, ViewResidentActivityForm, \
    ResidentActivityAnswerForm, ResidentActivityAddAnswerForm, AddVisitantSecurityForm, ViewResidentActivityAnswerForm
from info.info_viwes.condominium.report.report_view import visitant_report
from info.models import CondominiumProfile, Apartment, Block, Resident, HowTo, Visitant, VisitantReport, \
    ResidentActivity, ResidentActivityAnswer, VisitantRequiredFields, ResidentFeatures
from info.utils import get_condominium, add_signature_to_data, add_manager_notification, add_notification
from info.views import email, _add_resident_permission

FIXED_TZ = pytz.timezone("America/Sao_Paulo")
AUTO_DEPARTURE_NOTE = "[BAIXADO PELO SISTEMA]"

DUPLICATE_WINDOW_SECONDS = 30


def _is_duplicate_visitant(condominium, name, resident=None, vehicle_plate=None, arrived=None,
                           block=None, apartment=None):
    """Evita o reenvio acidental da MESMA liberação numa janela curta.

    Deduplica pela placa do veículo (identidade real) quando houver; senão,
    pelo nome. O estado ``arrived`` separa o fluxo de ENTRADA (arrived=False)
    do de SAÍDA (arrived=True), para que liberar entrada e saída do mesmo
    veículo em sequência nunca se anulem.
    """
    cutoff = datetime.datetime.now(FIXED_TZ) - datetime.timedelta(seconds=DUPLICATE_WINDOW_SECONDS)
    qs = Visitant.objects.filter(
        condominium=condominium,
        created__gte=cutoff,
    )
    if resident is not None:
        qs = qs.filter(resident=resident)
    if block is not None:
        qs = qs.filter(block=block)
    if apartment is not None:
        qs = qs.filter(apartment=apartment)

    normalized_plate = _normalize_visitant_plate(vehicle_plate)
    if normalized_plate:
        qs = qs.filter(vehicle_plate__iexact=normalized_plate)
    else:
        qs = qs.filter(name=name)

    if arrived is not None:
        qs = qs.filter(arrived=arrived)

    return qs.exists()


def _normalize_visitant_plate(vehicle_plate):
    if not vehicle_plate:
        return ""
    return str(vehicle_plate).replace(' ', '').replace('-', '')


def _vehicle_inside_block_enabled(condominium):
    """Chave liga/desliga do bloqueio de veiculo que consta dentro do condominio."""
    features, _ = ResidentFeatures.objects.get_or_create(condominium=condominium)
    return features.block_vehicle_inside


def _auto_visitant_leave_enabled(condominium):
    """Chave liga/desliga: portaria dá baixa na saída sem a liberação do cliente."""
    features, _ = ResidentFeatures.objects.get_or_create(condominium=condominium)
    return features.auto_visitant_leave


def _vehicle_inside_condominium(condominium, vehicle_plate):
    """Retorna o Visitant ativo (entrou e nao saiu) para a placa, ou None."""
    normalized_plate = _normalize_visitant_plate(vehicle_plate)
    if not normalized_plate:
        return None
    return Visitant.objects.filter(
        condominium=condominium,
        vehicle_plate__iexact=normalized_plate,
        visit_in__isnull=False,
        leaves_in__isnull=True,
        allowed=True,
    ).select_related('resident').order_by('-visit_in').first()


def _vehicle_inside_message(active_visitant, resident):
    inside_resident = active_visitant.resident
    local = ((active_visitant.block or "") + " / " + (active_visitant.apartment or "")).strip(" /")
    entrada = ""
    if active_visitant.visit_in:
        entrada = " (entrada em " + active_visitant.visit_in.astimezone(FIXED_TZ).strftime("%d/%m às %H:%M") + ")"

    if inside_resident and resident and inside_resident.pk == resident.pk:
        return ("Este veículo consta dentro do condomínio" + entrada +
                " porque a liberação anterior não recebeu baixa da portaria. Se ele já saiu, abra o "
                "histórico de liberações, exclua a liberação sem baixa (linha destacada em vermelho) "
                "e faça a nova liberação.")

    if resident is None:
        return ("Este veículo consta dentro do condomínio" + entrada +
                ", sem baixa de saída. Registre a saída dele antes de liberar nova entrada.")

    liberador = ""
    if inside_resident and getattr(inside_resident, 'condominium_name', None):
        liberador = inside_resident.condominium_name
    if not liberador and local:
        liberador = "morador do " + local
    if not liberador:
        liberador = "outro morador"
    return ("Este veículo já foi liberado por " + liberador + " e ainda consta dentro do condomínio" +
            entrada + ". Se ele já saiu, a portaria precisa registrar a saída ou quem liberou precisa "
            "excluir a liberação sem baixa no histórico de liberações.")


def _get_resident_obj(condominium, resident):
    name = (resident.condominium_name or "").strip()
    email = (resident.email or "").strip()
    base = Resident.objects.filter(apartment__block__condominium=condominium)
    qs = base.filter(name__iexact=name, email__iexact=email)
    if not qs.exists():
        qs = base.filter(email__iexact=email)
    if not qs.exists():
        qs = base.filter(name__iexact=name)
    return qs.first()


def _resident_block_apartment(resident_obj):
    if resident_obj is None:
        return "", ""
    apartment = resident_obj.apartment
    return apartment.block.name, str(apartment.number) + " " + apartment.complement


def _liberacao_notificacao(visitant, resident):
    local = (visitant.block + " / " + visitant.apartment).strip(" /")
    if local:
        return "NOVO VISITANTE LIBERADO PELO MORADOR DO " + local + "."
    nome = (resident.condominium_name or "morador").strip()
    return "NOVO VISITANTE LIBERADO PELO MORADOR " + nome + "."


def _append_auto_departure_note(comment):
    current_comment = (comment or "").strip()
    if AUTO_DEPARTURE_NOTE in current_comment:
        return current_comment
    if not current_comment:
        return AUTO_DEPARTURE_NOTE

    max_comment_length = 250
    allowed_prefix_length = max_comment_length - len(AUTO_DEPARTURE_NOTE) - 1
    return f"{current_comment[:allowed_prefix_length].rstrip()} {AUTO_DEPARTURE_NOTE}"


def _get_active_visitants_by_plate(condominium, vehicle_plate, exclude_pk=None):
    normalized_plate = _normalize_visitant_plate(vehicle_plate)
    if not normalized_plate:
        return []

    active_visitants = Visitant.objects.filter(
        condominium=condominium,
        leaves_in__isnull=True,
        arrived=True,
    ).exclude(
        vehicle_plate__isnull=True,
    ).exclude(
        vehicle_plate="",
    )

    if exclude_pk:
        active_visitants = active_visitants.exclude(pk=exclude_pk)

    return [
        active_visitant for active_visitant in active_visitants
        if _normalize_visitant_plate(active_visitant.vehicle_plate) == normalized_plate
    ]


def _close_active_visitants_by_plate(condominium, vehicle_plate, exclude_pk=None):
    active_visitants = _get_active_visitants_by_plate(condominium, vehicle_plate, exclude_pk=exclude_pk)

    closed_count = 0
    for active_visitant in active_visitants:
        active_visitant.comment = _append_auto_departure_note(active_visitant.comment)
        _departure_registration(active_visitant)
        closed_count += 1

    return closed_count


def _visitant_success_message(base_message, auto_closed_count):
    if auto_closed_count:
        return f"{base_message} {auto_closed_count} registro(s) anterior(es) com a mesma placa foram baixados automaticamente."
    return base_message


def _get_visitant_required_fields(condominium):
    mandatory, _ = VisitantRequiredFields.objects.get_or_create(condominium=condominium)
    return mandatory


def _configure_visitant_portaria_form(form, mandatory):
    form.fields['document'].required = mandatory.document
    form.fields['vehicle_model'].required = mandatory.allow_vehicle and mandatory.vehicle_model
    form.fields['vehicle_plate'].required = mandatory.allow_vehicle and mandatory.vehicle_plate
    form.fields['photo'].required = mandatory.photo


def _attach_visitant_photo_from_request(request, visitant, document_name):
    photo = request.FILES.get('photo') or None
    profile_pic = request.POST.get('webimg')

    if profile_pic and ',' in profile_pic:
        try:
            image_data = profile_pic.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            image_file = io.BytesIO(image_bytes)
            Image.open(image_file)
            image_file.seek(0)
            filename = f"{document_name or 'visitante'}.jpg"
            photo = InMemoryUploadedFile(
                image_file, None, filename, 'image/jpeg', len(image_bytes), None)
        except Exception:
            pass

    if photo:
        visitant.photo = photo

@login_required(login_url='info:sign-in')
def add_apartment(request):
    condominium = get_condominium(request)
    blocks = condominium.block_set.all()

    form = AddApartmentForm(request.POST or None, blocks=blocks)

    ApartmentFormset = modelformset_factory(Apartment, form=AddedApartmentForm, extra=0)
    queryset = Block.objects.none()
    formset = ApartmentFormset(request.POST or None, queryset=queryset)

    context = {'form': form,
               'formset': formset
               }

    if all([form.is_valid(), formset.is_valid()]):
        try:
            block = Block.objects.get(pk=form.cleaned_data['block'].id)
            Apartment.objects.get(block=block, number=int(form.cleaned_data['number']),
                                  complement=form.cleaned_data['complement'])
        except Apartment.DoesNotExist:
            apartment = Apartment()
            apartment.number = int(form.cleaned_data['number'])
            apartment.complement = form.cleaned_data['complement'] or ""
            apartment.block = block
            apartment.save()

        if request.POST.get("reply") is not None and request.POST.get("reply") == "on":
            for other_block in condominium.block_set.all():
                if other_block == block:
                    continue

                reply_apartment = Apartment()
                reply_apartment.number = int(form.cleaned_data['number'])
                reply_apartment.complement = form.cleaned_data['complement'] or ""
                reply_apartment.block = other_block

                try:
                    Apartment.objects.get(block=other_block, number=int(form.cleaned_data['number']),
                                          complement=form.cleaned_data['complement'])
                except Apartment.DoesNotExist:
                    reply_apartment.save()

        for added in formset:
            if added.has_changed():
                try:
                    Apartment.objects.get(block=block, number=int(added.cleaned_data['number']),
                                          complement=added.cleaned_data['complement'])
                except Apartment.DoesNotExist:
                    apartment = Apartment()
                    apartment.number = int(added.cleaned_data['number'])
                    apartment.complement = added.cleaned_data['complement'] or ""
                    apartment.block = block
                    apartment.save()

            if request.POST.get("reply") is not None and request.POST.get("reply") == "on":
                for other_block in condominium.block_set.all():
                    if other_block == block:
                        continue

                    if added.has_changed():
                        try:
                            Apartment.objects.get(block=other_block, number=int(added.cleaned_data['number']),
                                                  complement=added.cleaned_data['complement'])
                        except Apartment.DoesNotExist:
                            reply_apartment = Apartment()
                            reply_apartment.number = int(added.cleaned_data['number'])
                            reply_apartment.complement = added.cleaned_data['complement'] or ""
                            reply_apartment.block = other_block
                            reply_apartment.save()

        messages.success(request, "Apartamentos Cadastrados! Os apartamentos já cadastrados seão ignorados")
        return redirect('info:dashboard')

    else:
        print(form.errors)
        print(formset.errors)

    return render(request, "info/condominium/apartment/add_apartment.html", context=context)


@login_required(login_url='info:sign-in')
def add_block(request):
    condominium = get_condominium(request)

    form = AddBlockForm(request.POST or None)

    BlockFormset = modelformset_factory(Block, form=AddBlockForm, extra=0)
    queryset = Block.objects.none()
    formset = BlockFormset(request.POST or None, queryset=queryset, prefix="block")

    context = {'form': form,
               'formset': formset
               }

    if all([form.is_valid(), formset.is_valid()]):
        try:
            Block.objects.get(name__iexact=form.cleaned_data['name'], condominium=condominium)
            messages.error(request, "Já existe um bloco cadastrado como: " + form.cleaned_data[
                'name'] + ". Adicione com um nome diferente se necessário")
            return redirect('info:add-block')

        except Block.DoesNotExist:
            block = Block()
            block.name = form.cleaned_data['name']
            block.condominium = condominium
            block.save()

        for added in formset:
            if added.has_changed():
                try:
                    Block.objects.get(name__iexact=added.cleaned_data['name'], condominium=condominium)
                    messages.error(request, "Já existe um bloco cadastrado como: " + added.cleaned_data[
                        'name'] + ". Blocos anteriores a este foram adicionados.")
                    return redirect('info:add-block')
                except Block.DoesNotExist:
                    block = Block()
                    block.name = added.cleaned_data['name']
                    block.condominium = condominium
                    block.save()

        messages.success(request, "Blocos adicionados!")
        return redirect('info:dashboard')

    else:
        print(form.errors)
        print(formset.errors)

    return render(request, "info/condominium/apartment/add_block.html", context=context)


@login_required(login_url='info:sign-in')
def apartments(request):
    condominium = get_condominium(request)
    apartments_list = Apartment.objects.filter(block__condominium=condominium).order_by("block", "number")
    context = {'apartments': apartments_list,
               'user': condominium,
               }
    return render(request, "info/condominium/apartment/apartments.html", context=context)


@login_required(login_url='info:sign-in')
def blocks(request):
    condominium = get_condominium(request)
    block_list = Block.objects.filter(condominium=condominium).order_by("name")
    context = {'blocks': block_list,
               'user': condominium,
               }
    return render(request, "info/condominium/apartment/blocks.html", context=context)


@login_required(login_url='info:sign-in')
def delete_block(request, id):
    condominium = get_condominium(request)
    block = get_object_or_404(Block, pk=int(id), condominium=condominium)
    block.delete()
    messages.success(request, "Bloco Removido!")
    return redirect(reverse('info:blocks'))


@login_required(login_url='info:sign-in')
def update_block(request, id):
    condominium = get_condominium(request)
    block = get_object_or_404(Block, pk=int(id), condominium=condominium)

    form = AddBlockForm(instance=block)

    context = {'form': form}

    if request.method == 'POST':
        form = AddBlockForm(request.POST)

        if form.is_valid():
            block.name = form.cleaned_data['name']
            block.save()

        messages.success(request, "Bloco atualizado!")
        return redirect('info:blocks')

    else:
        print(form.errors)

    return render(request, "info/condominium/apartment/update_block.html", context=context)


@login_required(login_url='info:sign-in')
def update_apartment(request, id):
    condominium = get_condominium(request)
    apartment = get_object_or_404(Apartment, pk=int(id), block__condominium=condominium)

    form = AddedApartmentForm(instance=apartment)

    context = {'form': form}

    if request.method == 'POST':
        form = AddedApartmentForm(request.POST)

        if form.is_valid():
            apartment.number = int(form.cleaned_data['number'])
            apartment.complement = form.cleaned_data['complement'] or ""
            apartment.save()

            messages.success(request, "Apartamento atualizado!")
            return redirect('info:apartments')

        else:
            print(form.errors)

    return render(request, "info/condominium/apartment/update_apartment.html", context=context)


@login_required(login_url='info:sign-in')
def delete_apartment(request, id):
    condominium = get_condominium(request)
    apartment = get_object_or_404(Apartment, pk=int(id), block__condominium=condominium)
    apartment.delete()
    messages.success(request, "Apartamento Removido!")
    return redirect(reverse('info:apartments'))


@login_required(login_url='info:sign-in')
def add_resident(request):
    condominium = get_condominium(request)
    blocks = Block.objects.filter(condominium=condominium)
    # apartments =

    if request.method == "POST":

        apartment = Apartment.objects.get(pk=int(request.POST.get('apartment')))

        error = False

        if request.POST.get("default_pass") is not None and request.POST.get("default_pass") == "on":
            password = request.POST.get("new_password1")
            confirmation = request.POST.get("new_password2")

            try:
                if len(password) != 4:
                    messages.error("A senha deve conter 4 dígitos")
                    error = True
                elif int(password) == int(confirmation):
                    user = CondominiumProfile()
                    user.condominium_name = request.POST.get('name')
                    user.email = str(request.POST.get('email')).lower()
                    user.resident_in = condominium
                    user.plan_expiration = condominium.plan_expiration
                    user.whatsapp = request.POST.get('whatsapp') or ""
                    user.set_password(password)
                    user.is_active = True
                    user.email_verified = True
                    user.added_by_link = False

                    if request.FILES.get("image"):
                        user.profile_pic = request.FILES.get("image")

                    user.use_tabs = condominium.use_tabs
                    try:
                        user.save()
                        _add_resident_permission(user)
                    except IntegrityError:
                        messages.error(request, "Já existe um usuário cadastrado com este email")
                        error = True

                else:
                    messages.error(request, "As senhas não são iguais")
                    error = True
            except ValueError:
                messages.error(request, "As senhas devem conter apenas números")
                error = True

        if not error:

            if request.POST.get("remove") is not None and request.POST.get("remove") == "on":
                residents = Resident.objects.filter(apartment=apartment)
                for resident in residents:
                    try:
                        user = CondominiumProfile.objects.get(email=resident.email, condominium_name=resident.name)
                        user.delete()
                    except CondominiumProfile.DoesNotExist:
                        pass

                    resident.delete()

            resident = Resident()
            resident.name = request.POST.get('name')
            resident.email = str(request.POST.get('email')).lower()
            resident.kind = request.POST.get('kind')
            resident.whatsapp = request.POST.get('whatsapp') or ""
            resident.apartment = apartment
            resident.save()

            messages.success(request, "Cadastro realizado!")
            return redirect(reverse('info:residents'))

    form = AddResidentForm(request.POST or None, blocks=blocks)
    context = {'form': form,
               }
    return render(request, "info/condominium/apartment/add_resident.html", context=context)


@login_required(login_url='info:sign-in')
def update_resident(request, id):
    condominium = get_condominium(request)
    resident = get_object_or_404(Resident, pk=id, apartment__block__condominium=condominium)

    form = UpdateResidentForm(instance=resident)

    if request.method == "POST":

        # form = UpdateResidentForm(request.POST)
        # if form.is_valid():

        resident.name = request.POST.get('name') or resident.name
        resident.email = str(request.POST.get('email')).lower() or resident.email
        resident.kind = request.POST.get('kind') or resident.kind
        resident.whatsapp = request.POST.get('whatsapp') or resident.whatsapp

        resident.save()

        messages.success(request, "Morador atualizado!")

        return redirect(reverse('info:dashboard'))
    else:
        print(form.errors)

    context = {'form': form,
               'profile': resident
               }
    return render(request, "info/condominium/apartment/update_resident.html", context=context)


@login_required(login_url='info:sign-in')
def delete_resident(request, id):
    condominium = get_condominium(request)
    try:
        resident = Resident.objects.get(pk=id, apartment__block__condominium=condominium)
        resident.delete()
    except Resident.DoesNotExist:
        messages.error(request, "Morador não encontrado!")
        return redirect(reverse('info:residents'))

    try:
        user = CondominiumProfile.objects.get(resident_in=resident.apartment.block.condominium, email=resident.email)
        user.delete()
    except CondominiumProfile.DoesNotExist:
        pass

    messages.success(request, "Morador removido!")
    return redirect(reverse('info:residents'))


@login_required(login_url='info:sign-in')
def get_apartments(request):
    block = request.GET.get('block_id')
    if block:
        apartments = Apartment.objects.filter(block=block).order_by('number')
        data = [{'id': apartment.id, 'name': str(apartment.number) + " " + apartment.complement}
                for apartment in apartments]
    else:
        data = []
    return JsonResponse(data, safe=False)


@login_required(login_url='info:sign-in')
def get_residents(request):
    apartment = request.GET.get('apartment_id')
    if apartment:
        residents = Resident.objects.filter(apartment=apartment).order_by('name')
        data = [{'id': resident.id, 'name': resident.name}
                for resident in residents]
    else:
        data = []
    return JsonResponse(data, safe=False)


@login_required(login_url='info:sign-in')
def residents(request):
    condominium = get_condominium(request)

    if request.method == 'POST':
        is_defaulter = request.POST.get('is_defaulter')
        resident = Resident.objects.get(pk=int(request.POST.get('defaulter_id')))
        try:
            user = CondominiumProfile.objects.get(email=resident.email, condominium_name=resident.name)

        except CondominiumProfile.DoesNotExist:
            user = None

        if is_defaulter and is_defaulter == "on":

            resident.defaulter = True
            if user:
                user.defaulter = True
        else:
            resident.defaulter = False
            if user:
                user.defaulter = False

        resident.save()
        if user:
            user.save()

        messages.success(request, "Morador atualizado!")

    residents_list = Resident.objects.filter(apartment__block__condominium=condominium).order_by("apartment__block")

    search_name = request.GET.get('resident_name')
    search_block = request.GET.get('resident_block')
    search_apartment = request.GET.get('resident_apartment')
    search_complement = request.GET.get('resident_complement')

    if search_name:
        residents_list = residents_list.filter(name__contains=search_name)

    if search_block:
        residents_list = residents_list.filter(apartment__block__name__contains=search_block)

    if search_apartment:
        residents_list = residents_list.filter(apartment__number__exact=int(search_apartment))

    if search_complement:
        residents_list = residents_list.filter(apartment__complement__contains=search_complement)

    # Paginate the queryset
    paginator = Paginator(residents_list, 20)  # Show 20 visitants per page
    page_number = request.GET.get('page')  # Get the page number from the request
    page_obj = paginator.get_page(page_number)

    # users_to_aprove = residents_list = CondominiumProfile.objects.filter(resident_in=condominium, added_by_link=True,
    #                                                                      is_active=False).order_by("-created")
    context = {'residents': page_obj,
               'page_obj': page_obj,
               'user': condominium
               # 'users_to_aprove': users_to_aprove,
               }

    how_to_residents = HowTo.objects.get(name__exact="Moradores > Listagem")
    if how_to_residents.kind == "Texto":
        context['how_to_residents_text'] = how_to_residents.value
    else:
        context['how_to_residents_link'] = how_to_residents.value
    return render(request, "info/condominium/apartment/residents.html", context=context)


@login_required(login_url='info:sign-in')
def view_resident(request, id):
    condominium = get_condominium(request)
    resident = get_object_or_404(Resident, pk=id, apartment__block__condominium=condominium)
    profile = CondominiumProfile.objects.get(email=resident.email, condominium_name=resident.name,
                                             resident_in=resident.apartment.block.condominium)

    form = ViewUserForm(instance=profile)

    context = {'form': form,
               'id': profile.id
               }

    if profile.profile_pic:
        context['img'] = profile.profile_pic

    return render(request, "info/condominium/apartment/view_resident.html", context=context)


@login_required(login_url='info:sign-in')
def approve_residents(request):
    condominium = get_condominium(request)

    if request.method == "POST":

        approve_choice = request.POST.get('approve')

        if approve_choice and approve_choice == "on":
            condominium.auto_approve = True
        else:
            condominium.auto_approve = False
        condominium.save()

    users_to_approve = CondominiumProfile.objects.filter(resident_in=condominium, added_by_link=True,
                                                         is_active=False, email_verified=True).order_by("-created")
    if condominium.auto_approve:
        for user in users_to_approve:
            user.is_active = True
            user.save()

            subject = 'Comunicado do ' + user.resident_in.condominium_name
            data = add_signature_to_data(request)
            data['message'] = "Seu usuário foi ativado. Faça o login através do botão abaixo."
            data['link'] = True
            current_site = get_current_site(request)
            data['domain'] = current_site.domain
            html_content = render_to_string(
                'info/condominium/messages/message.html',
                data
            )

            text_content = strip_tags(html_content)
            msg = EmailMultiAlternatives(subject, text_content, to=[user.email])
            msg.attach_alternative(html_content, "text/html")

            msg.send()

        users_to_approve = CondominiumProfile.objects.none()

    residents = []

    for user in users_to_approve:
        residents.append(Resident.objects.get(email=user.email, name=user.condominium_name,
                                              apartment__block__condominium=condominium))
    context = {'residents': residents,
               'approve': condominium.auto_approve,
               'user': condominium
               }
    return render(request, "info/condominium/apartment/approve_residents.html", context=context)


@login_required(login_url='info:sign-in')
def approve_resident(request, id):
    profile = get_object_or_404(CondominiumProfile, pk=id)
    profile.is_active = True
    profile.save()

    subject = 'Comunicado do ' + profile.resident_in.condominium_name
    data = add_signature_to_data(request)
    data['message'] = "Seu usuário foi ativado. Faça o login através do botão abaixo."
    data['link'] = True
    current_site = get_current_site(request)
    data['domain'] = current_site.domain
    html_content = render_to_string(
        'info/condominium/messages/message.html',
        data
    )

    text_content = strip_tags(html_content)
    msg = EmailMultiAlternatives(subject, text_content, to=[profile.email])
    msg.attach_alternative(html_content, "text/html")

    msg.send()

    messages.success(request, "Usuário Aprovado!")
    return redirect(reverse('info:approve-residents'))


@login_required(login_url='info:sign-in')
def reprove_resident(request, id):
    profile = get_object_or_404(CondominiumProfile, pk=id)

    subject = 'Comunicado do ' + profile.resident_in.condominium_name
    data = add_signature_to_data(request)
    data['message'] = "Seu usuário foi rejeitado pelo administrador." \
                      "Faça um novo registro ou entre em contato com a administração."
    html_content = render_to_string(
        'info/condominium/messages/message.html',
        data
    )

    text_content = strip_tags(html_content)
    msg = EmailMultiAlternatives(subject, text_content, to=[profile.email])
    msg.attach_alternative(html_content, "text/html")

    msg.send()

    profile.delete()

    messages.success(request, "Usuário Reprovado!")
    return redirect(reverse('info:approve-residents'))


def register_resident(request):
    condominium = get_condominium(request)
    blocks = Block.objects.filter(condominium=condominium)
    # apartments =

    if request.method == "POST":

        apartment = Apartment.objects.get(pk=int(request.POST.get('apartment')))

        if request.POST.get("remove") is not None and request.POST.get("remove") == "on":
            residents = Resident.objects.filter(apartment=apartment)
            for resident in residents:
                resident.delete()

        resident = Resident()
        resident.name = request.POST.get('name')
        resident.email = str(request.POST.get('email')).lower()
        resident.kind = request.POST.get('kind')
        resident.apartment = apartment
        resident.save()

        messages.success(request, "Cadastro realizado!")

        return redirect(reverse('info:dashboard'))

    form = AddResidentForm(request.POST or None, blocks=blocks)
    context = {'form': form,
               }
    return render(request, "info/condominium/apartment/add_resident.html", context=context)


@login_required(login_url='info:sign-in')
def visitant_mandatory_fields(request):
    condominium = get_condominium(request)

    try:
        mandatory = VisitantRequiredFields.objects.get(condominium=condominium)
    except VisitantRequiredFields.DoesNotExist:
        mandatory = VisitantRequiredFields()
        mandatory.condominium = condominium
        mandatory.save()

    if request.method == 'POST':
        mandatory.document = request.POST.get("document") is not None and request.POST.get("document") == "on"
        mandatory.security_name = request.POST.get("security_name") is not None and request.POST.get(
            "security_name") == "on"
        mandatory.allow_vehicle = request.POST.get("allow_vehicle") is not None and request.POST.get(
            "allow_vehicle") == "on"
        mandatory.vehicle_model = request.POST.get("vehicle_model") is not None and request.POST.get(
            "vehicle_model") == "on"
        mandatory.vehicle_plate = request.POST.get("vehicle_plate") is not None and request.POST.get(
            "vehicle_plate") == "on"
        mandatory.photo = request.POST.get("photo") is not None and request.POST.get("photo") == "on"
        mandatory.pic = request.POST.get("pic") is not None and request.POST.get("pic") == "on"
        mandatory.save()
        messages.success(request, "Configuração atualizada!")
        return redirect(reverse('info:condominium-visitants'))

    context = {'mandatory': mandatory,
               }
    return render(request, "info/condominium/apartment/visitant_mandatory_fields.html", context=context)


@login_required(login_url='info:sign-in')
@permission_required('info.add_visitant', login_url='info:sign-in')
def resident_visitants(request):
    condominium = get_condominium(request)
    resident = CondominiumProfile.objects.get(pk=int(request.user.id))
    visitants = Visitant.objects.filter(condominium=condominium, resident=resident, allowed=True).order_by("-created")

    visitants_list = []
    for visitant in visitants:
        visitant_obj = {'id': visitant.id, 'name': visitant.name, 'comment': visitant.comment, 'until': visitant.until,
                        'vehicle_plate': visitant.vehicle_plate, 'vehicle_model': visitant.vehicle_model,
                        'leaves': visitant.leaves_in,
                        'visit': visitant.visit_in, 'can_leave': visitant.can_leave}
        print(visitant.until.date(), condominium.plan_expiration)
        if visitant.until.date() == condominium.plan_expiration:
            visitant_obj['is_permanent'] = True
        else:
            visitant_obj['is_permanent'] = False
        visitants_list.append(visitant_obj)

    context = {'visitants_list': visitants_list,
               }

    how_to_resident_visitants = HowTo.objects.get(name__exact="Moradores > Visitantes")
    if how_to_resident_visitants.kind == "Texto":
        context['how_to_resident_visitants_text'] = how_to_resident_visitants.value
    else:
        context['how_to_resident_visitants_link'] = how_to_resident_visitants.value

    return render(request, "info/condominium/apartment/resident_visitants.html", context=context)


@login_required(login_url='info:sign-in')
def reset_password(request, id):
    condominium = get_condominium(request)
    resident = get_object_or_404(Resident, pk=id, apartment__block__condominium=condominium)
    request.session['resident_id'] = id
    try:
        profile = CondominiumProfile.objects.get(condominium_name=resident.name, email=resident.email,
                                                 resident_in=condominium)
        context = {'profile': profile,
                   'resident': resident
                   }
        return render(request, 'info/condominium/apartment/reset_password.html', context=context)
    except CondominiumProfile.DoesNotExist:
        messages.error(request, "Morador ainda não cadastrado como usuário!")
        return redirect(reverse('info:update-resident', args=[int(id)]))


@login_required(login_url='info:sign-in')
def confirm_manager_reset_password(request, id):
    condominium = get_condominium(request)
    profile = get_object_or_404(CondominiumProfile, pk=id, resident_in=condominium)
    profile.set_password("1234")
    profile.save()
    messages.success(request, "Senha resetada para 1234")
    return redirect(reverse('info:update-resident', args=[int(request.session['resident_id'])]))


@login_required(login_url='info:sign-in')
def add_visitant(request):
    condominium = get_condominium(request)
    resident = CondominiumProfile.objects.get(pk=int(request.user.id))

    form = AddVisitantForm(request.POST or None, files=request.FILES or None)

    resident_obj = _get_resident_obj(condominium, resident)

    try:
        mandatory = VisitantRequiredFields.objects.get(condominium=condominium)
    except VisitantRequiredFields.DoesNotExist:
        mandatory = VisitantRequiredFields()
        mandatory.condominium = condominium
        mandatory.save()

    form.fields['vehicle_plate'].required = mandatory.allow_vehicle and mandatory.vehicle_plate
    form.fields['check_photo'].required = mandatory.photo

    if request.method == "POST":
        if form.is_valid():
            visitant_name = form.cleaned_data['name']
            visitant_plate = _normalize_visitant_plate(form.cleaned_data.get('vehicle_plate'))
            active_inside = None
            if _vehicle_inside_block_enabled(condominium):
                active_inside = _vehicle_inside_condominium(condominium, visitant_plate)
            if active_inside:
                messages.error(request, _vehicle_inside_message(active_inside, resident))
                features_ctx, _ = ResidentFeatures.objects.get_or_create(condominium=condominium)
                return render(request, "info/condominium/apartment/add_visitant.html",
                              context={'form': form, 'mandatory': mandatory,
                                       'permanent': features_ctx.permanent})
            if _is_duplicate_visitant(condominium, visitant_name, resident=resident,
                                      vehicle_plate=visitant_plate, arrived=False):
                messages.success(request, "Liberação realizada!")
                return redirect(reverse('info:dashboard'))

            visitant = Visitant()
            visitant.condominium = condominium
            visitant.block, visitant.apartment = _resident_block_apartment(resident_obj)
            visitant.name = visitant_name
            visitant.vehicle_plate = visitant_plate
            visitant.check_photo = form.cleaned_data.get('check_photo')
            visitant.until = condominium.plan_expiration if form.cleaned_data.get('permanent') else form.cleaned_data.get('until')
            visitant.leave_consent = request.POST.get('leave_consent') == 'on'
            visitant.comment = form.cleaned_data.get('comment')
            visitant.delivery_code = form.cleaned_data.get('delivery_code') or ""
            visitant.resident = resident

            visitant.save()
            messages.success(request, "Liberação realizada!")
            add_manager_notification(condominium,
                                     _liberacao_notificacao(visitant, resident))

            return redirect(reverse('info:dashboard'))

    features, _ = ResidentFeatures.objects.get_or_create(condominium=condominium)
    context = {'form': form, 'mandatory': mandatory, 'permanent': features.permanent
               }
    return render(request, "info/condominium/apartment/add_visitant.html", context=context)


@login_required(login_url='info:sign-in')
def add_internal_leave(request):
    condominium = get_condominium(request)
    resident = CondominiumProfile.objects.get(pk=int(request.user.id))

    form = AddVisitantForm(request.POST or None, files=request.FILES or None)

    resident_obj = _get_resident_obj(condominium, resident)

    try:
        mandatory = VisitantRequiredFields.objects.get(condominium=condominium)
    except VisitantRequiredFields.DoesNotExist:
        mandatory = VisitantRequiredFields()
        mandatory.condominium = condominium
        mandatory.save()

    form.fields['vehicle_plate'].required = mandatory.allow_vehicle and mandatory.vehicle_plate
    form.fields['check_photo'].required = mandatory.photo

    if request.method == "POST":
        if form.is_valid():
            visitant_name = form.cleaned_data['name']
            visitant_plate = _normalize_visitant_plate(form.cleaned_data.get('vehicle_plate'))
            if _is_duplicate_visitant(condominium, visitant_name, resident=resident,
                                      vehicle_plate=visitant_plate, arrived=True):
                messages.success(request, "Liberação realizada!")
                return redirect(reverse('info:dashboard'))

            visitant = Visitant()
            visitant.condominium = condominium
            visitant.block, visitant.apartment = _resident_block_apartment(resident_obj)
            visitant.name = visitant_name
            visitant.vehicle_plate = visitant_plate
            visitant.check_photo = form.cleaned_data.get('check_photo')
            visitant.until = condominium.plan_expiration if form.cleaned_data.get('permanent') else form.cleaned_data.get('until')
            visitant.comment = form.cleaned_data.get('comment')
            visitant.resident = resident
            visitant.visit_in = datetime.datetime.now(FIXED_TZ)
            visitant.arrived = True
            visitant.can_leave = True

            visitant.save()
            messages.success(request, "Liberação realizada!")
            add_manager_notification(condominium,
                                     _liberacao_notificacao(visitant, resident))

            return redirect(reverse('info:dashboard'))

    features, _ = ResidentFeatures.objects.get_or_create(condominium=condominium)
    context = {'form': form, 'mandatory': mandatory, 'permanent': features.permanent
               }
    return render(request, "info/condominium/apartment/add_internal_leave.html", context=context)


@login_required(login_url='info:sign-in')
def condominium_visitants(request):
    condominium = get_condominium(request)
    user = CondominiumProfile.objects.get(pk=int(request.user.id))

    # Base query for visitants
    visitants = Visitant.objects.filter(
        condominium=condominium,
        allowed=True
    ).filter(
        Q(leaves_in=None) | Q(until__exact=condominium.plan_expiration)
    ).annotate(
        count=Count('id', filter=Q(leaves_in=None, visit_in__isnull=False))
    ).order_by("-created")

    # Apply search filters
    search_resident = request.GET.get('search_resident')
    search_plate = request.GET.get('visitant_plate')
    search_model = request.GET.get('visitant_model')
    search_apartment = request.GET.get('block_apartment')

    if search_resident:
        visitants = visitants.filter(resident__condominium_name__icontains=search_resident)

    if search_plate:
        visitants = visitants.filter(vehicle_plate__icontains=search_plate)

    if search_model:
        visitants = visitants.filter(vehicle_model__icontains=search_model)

    if search_apartment:
        visitants = visitants.filter(
            Q(block__icontains=search_apartment) | Q(apartment__icontains=search_apartment)
        )

    # Paginate the queryset
    paginator = Paginator(visitants, 20)  # Show 20 visitants per page
    page_number = request.GET.get('page')  # Get the page number from the request
    page_obj = paginator.get_page(page_number)  # Get the page object

    auto_leave = _auto_visitant_leave_enabled(condominium)

    visitants_list = []
    for visitant in page_obj:
        # Collecting visitant data for each visitant
        visitant_obj = {
            'id': visitant.id,
            'vehicle_plate': visitant.vehicle_plate if visitant.vehicle_plate else "",
            'name': visitant.name,
            'vehicle_model': visitant.vehicle_model if visitant.vehicle_model else "",
            'comment': visitant.comment if visitant.comment else "",
            'until': visitant.until,
            'apartment': f"{visitant.block}/{visitant.apartment}",
            'resident': visitant.resident.condominium_name if visitant.resident else "",
            'leaves': visitant.leaves_in,
            'visit': visitant.visit_in,
            'count': visitant.count,  # Annotated count
            'can_leave': visitant.can_leave or auto_leave,
            'arrived': visitant.arrived,
            'delivery_code': visitant.delivery_code if visitant.delivery_code else "",
        }

        if visitant.visit_in:
            visitant_obj['visit_in'] = visitant.visit_in.isoformat()

        if visitant.visit_time:
            # Calculate duration time
            days, seconds = divmod(visitant.visit_time.total_seconds(), 86400)
            hours, remainder = divmod(seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            if days:
                dur_string = f"{int(days)} days, {int(hours):02}:{int(minutes):02}:{int(seconds):02}"
            else:
                dur_string = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

            visitant_obj['visit_time'] = dur_string

        visitant_obj['is_permanent'] = visitant.until.date() == condominium.plan_expiration

        visitants_list.append(visitant_obj)

    # Reduce number of queries by using a count directly on the base queryset
    now = datetime.datetime.now(FIXED_TZ)
    vehicle_counter = Visitant.objects.filter(
        ~Q(visit_in=None),
        ~Q(vehicle_plate=""),
        leaves_in=None,
        condominium=condominium,
        arrived=True,
        until__gte=now
    ).count()

    context = {
        'visitants_list': visitants_list,
        'vehicle_counter': vehicle_counter,
        'employee': True if user.work_for else False,
        'page_obj': page_obj  # Pass the paginated page object to the template
    }

    return render(request, "info/condominium/apartment/condominium_visitants.html", context=context)


@login_required(login_url='info:sign-in')
def visitant_arrival(request, id):
    condominium = get_condominium(request)
    visitant = get_object_or_404(Visitant, pk=int(id), condominium=condominium)
    mandatory = _get_visitant_required_fields(condominium)

    form = RegisterVisitant(request.POST or None, files=request.FILES or None, instance=visitant)
    _configure_visitant_portaria_form(form, mandatory)

    if request.method == "POST":
        if form.is_valid():
            visitant.document = form.cleaned_data['document']
            visitant.vehicle_model = form.cleaned_data['vehicle_model'] or ""
            visitant.vehicle_plate = _normalize_visitant_plate(form.cleaned_data['vehicle_plate'])

            _close_active_visitants_by_plate(condominium, visitant.vehicle_plate, exclude_pk=visitant.pk)

            visitant.visit_in = datetime.datetime.now(FIXED_TZ)
            visitant.leaves_in = None
            visitant.arrived = True
            visitant.visit_time = None
            visitant.can_leave = False

            _attach_visitant_photo_from_request(request, visitant, visitant.document)

            visitant.security_name = request.user.condominium_name
            visitant.save()

            messages.success(request, "Registro realizado!")
            return redirect(reverse('info:condominium-visitants'))
        else:
            import logging
            logger = logging.getLogger('info.visitant_arrival')
            logger.warning(
                f"[REGISTRO FALHOU] visitant_id={visitant.id} "
                f"condominium={condominium.id} "
                f"form_errors={form.errors.as_json()}"
            )

    context = {'form': form, 'mandatory': mandatory, 'visitant': visitant}

    if visitant.check_photo:
        context['img'] = visitant.check_photo

    return render(request, "info/condominium/apartment/register_visitant.html", context=context)


@login_required(login_url='info:sign-in')
def add_visitant_security(request):
    condominium = get_condominium(request)
    blocks = Block.objects.filter(condominium=condominium)
    mandatory = _get_visitant_required_fields(condominium)

    form = AddVisitantSecurityForm(request.POST or None, request.FILES or None, blocks=blocks)
    _configure_visitant_portaria_form(form, mandatory)

    if request.method == "POST":
        if form.is_valid():
            visitant_name = form.cleaned_data['name']
            dedup_apartment = form.cleaned_data['apartment']
            visitant_plate = _normalize_visitant_plate(form.cleaned_data.get('vehicle_plate'))
            active_inside = None
            if _vehicle_inside_block_enabled(condominium):
                active_inside = _vehicle_inside_condominium(condominium, visitant_plate)
            if active_inside:
                messages.error(request, _vehicle_inside_message(active_inside, None))
                context = {'form': form, 'mandatory': mandatory}
                return render(request, "info/condominium/apartment/add_visitant_security.html", context=context)
            if _is_duplicate_visitant(condominium, visitant_name,
                                      vehicle_plate=visitant_plate,
                                      arrived=False,
                                      block=form.cleaned_data['block'].name,
                                      apartment=f"{dedup_apartment.number} {dedup_apartment.complement}"):
                messages.success(request, "Liberação realizada!")
                return redirect(reverse('info:condominium-visitants'))

            visitant = Visitant()
            apartment = form.cleaned_data['apartment']
            residents = Resident.objects.filter(apartment=apartment)

            resident_obj = None
            user = None
            for resident in residents:
                try:
                    user = CondominiumProfile.objects.get(condominium_name=resident.name, email=resident.email)
                    resident_obj = resident
                    break
                except CondominiumProfile.DoesNotExist:
                    continue

            block = form.cleaned_data['block']
            visitant.condominium = condominium
            visitant.block = block.name
            visitant.apartment = f"{resident_obj.apartment.number} {resident_obj.apartment.complement }" if resident_obj else f"{apartment.number} {apartment.complement}"
            visitant.name = visitant_name
            visitant.until = form.cleaned_data['until']
            visitant.comment = form.cleaned_data['comment']
            visitant.resident = user
            visitant.document = form.cleaned_data['document']
            visitant.vehicle_model = form.cleaned_data['vehicle_model'] or ""
            visitant.vehicle_plate = _normalize_visitant_plate(form.cleaned_data['vehicle_plate'])
            _attach_visitant_photo_from_request(request, visitant, visitant.document)

            visitant.security_name = request.user.condominium_name

            visitant.save()
            messages.success(request, "Liberação realizada!")

            return redirect(reverse('info:condominium-visitants'))

    context = {'form': form, 'mandatory': mandatory
               }

    return render(request, "info/condominium/apartment/add_visitant_security.html", context=context)


def _departure_registration(visitant):
    visitant.leaves_in = datetime.datetime.now(FIXED_TZ)
    visitant.arrived = False
    visitant.can_leave = False

    visit_in = visitant.visit_in
    if visit_in is not None and visit_in.tzinfo is None:
        visit_in = FIXED_TZ.localize(visit_in)
    visitant.visit_time = (visitant.leaves_in - visit_in) if visit_in else None

    Visitant.objects.filter(pk=visitant.pk).update(
        leaves_in=visitant.leaves_in,
        arrived=False,
        can_leave=False,
        visit_time=visitant.visit_time,
        comment=visitant.comment,
    )

    visitant_report = VisitantReport()
    visitant_report.condominium = visitant.condominium
    visitant_report.block = visitant.block
    visitant_report.apartment = visitant.apartment
    visitant_report.name = visitant.name
    visitant_report.document = visitant.document
    visitant_report.comment = visitant.comment
    visitant_report.until = visitant.until
    visitant_report.allowed = visitant.allowed
    visitant_report.security_name = visitant.security_name
    visitant_report.visit_in = visitant.visit_in
    visitant_report.leaves_in = visitant.leaves_in
    if visitant.photo and visitant.photo.storage.exists(visitant.photo.name):
        visitant_report.photo = visitant.photo
    visitant_report.vehicle_model = visitant.vehicle_model
    visitant_report.vehicle_plate = visitant.vehicle_plate
    visitant_report.resident = visitant.resident
    visitant_report.save()


@login_required(login_url='info:sign-in')
def visitant_departure(request, id):
    condominium = get_condominium(request)
    visitant = get_object_or_404(Visitant, pk=int(id), condominium=condominium)

    if visitant.leaves_in is None and not visitant.can_leave and not _auto_visitant_leave_enabled(condominium):
        messages.error(request, "O cliente ainda não liberou a saída deste veículo. "
                                "Entre em contato com a empresa e solicite a liberação.")
        return redirect(reverse('info:condominium-visitants'))

    closed_count = 0
    if visitant.leaves_in is None:
        _departure_registration(visitant)
        closed_count = 1
    closed_count += _close_active_visitants_by_plate(condominium, visitant.vehicle_plate, exclude_pk=visitant.pk)
    if not closed_count:
        messages.info(request, "Saída já registrada para este visitante.")
        return redirect(reverse('info:condominium-visitants'))

    if closed_count > 1:
        messages.success(request, f"{closed_count} liberações baixadas para a mesma placa!")
    else:
        messages.success(request, "Registro realizado!")
    return redirect(reverse('info:condominium-visitants'))


@login_required(login_url='info:sign-in')
def allow_departure(request, id):
    condominium = get_condominium(request)
    visitant = get_object_or_404(Visitant, pk=int(id), condominium=condominium)
    Visitant.objects.filter(pk=visitant.pk).update(can_leave=True)

    messages.success(request, "Saída Liberada!")
    add_manager_notification(visitant.condominium,
                             "SAÍDA DO VISITANTE " + (visitant.name or "") + " LIBERADA PELO MORADOR DO "
                             + (visitant.block or "") + " / " + (visitant.apartment or "") + ".")
    return redirect(reverse('info:resident-visitants'))


def _removal_report(visitant):
    visitant_report = VisitantReport()
    visitant_report.condominium = visitant.condominium
    visitant_report.block = visitant.block
    visitant_report.apartment = visitant.apartment
    visitant_report.name = visitant.name
    visitant_report.document = visitant.document
    visitant_report.comment = visitant.comment
    visitant_report.until = visitant.until
    visitant_report.allowed = visitant.allowed
    visitant_report.security_name = visitant.security_name
    visitant_report.visit_in = visitant.visit_in
    visitant_report.leaves_in = visitant.leaves_in
    if visitant.photo and visitant.photo.storage.exists(visitant.photo.name):
        visitant_report.photo = visitant.photo
    visitant_report.vehicle_model = visitant.vehicle_model
    visitant_report.vehicle_plate = visitant.vehicle_plate
    visitant_report.resident = visitant.resident
    visitant_report.save()


@login_required(login_url='info:sign-in')
def remove_visitant(request, id):
    condominium = get_condominium(request)
    visitant = get_object_or_404(Visitant, pk=int(id), condominium=condominium)

    updates = {'allowed': False, 'arrived': False}
    if visitant.visit_in and not visitant.leaves_in:
        updates['leaves_in'] = datetime.datetime.now(FIXED_TZ)
        updates['comment'] = ((visitant.comment or "") +
                              " [LIBERAÇÃO EXCLUÍDA PELO CLIENTE SEM BAIXA DA PORTARIA]").strip()[:250]
    Visitant.objects.filter(pk=visitant.pk).update(**updates)

    if 'leaves_in' in updates:
        visitant.leaves_in = updates['leaves_in']
        visitant.comment = updates['comment']
        _removal_report(visitant)

    messages.success(request, "Visitante removido!")
    add_manager_notification(visitant.condominium,
                             "VISITANTE " + (visitant.name or "") + " NÃO ESTÁ MAIS LIBERADO PELO MORADOR DO "
                             + (visitant.block or "") + " / " + (visitant.apartment or "") + ".")
    return redirect(reverse('info:resident-visitants'))


@login_required(login_url='info:sign-in')
def hide_contact(request):
    resident = CondominiumProfile.objects.get(pk=int(request.user.id))
    resident_obj = Resident.objects.get(name=resident.condominium_name, email=resident.email)

    if request.method == "POST":
        resident.hide_contact = request.POST.get("hide") is not None and request.POST.get("hide") == "on"
        resident.save()
        resident_obj.hide_contact = resident.hide_contact
        resident_obj.save()

        messages.success(request, "Atualizado com sucesso!")

        return redirect(reverse('info:dashboard'))

    context = {'user': resident,
               }
    return render(request, "info/condominium/apartment/hide_contact.html", context=context)


@login_required(login_url='info:sign-in')
@permission_required('info.my_activity', login_url='info:sign-in')
def my_activities(request):
    condominium = get_condominium(request)
    user = CondominiumProfile.objects.get(pk=int(request.user.id))
    resident = Resident.objects.get(name=user.condominium_name, email=user.email)

    activities = ResidentActivity.objects.filter(condominium=condominium, apartment=resident.apartment).order_by(
        "-created")

    activities |= ResidentActivity.objects.filter(condominium=condominium, resident_responsible=user).order_by(
        "-created")

    search_protocol = request.GET.get('protocol')
    search_title = request.GET.get('title')
    search_status = request.GET.get('status_filter')

    if search_protocol:
        activities = activities.filter(protocol__contains=search_protocol)

    if search_title:
        activities = activities.filter(title__contains=search_title)

    if search_status:
        activities = activities.filter(status=search_status)

    context = {'activities': activities,
               'user': condominium}

    return render(request, "info/condominium/apartment/my_activities.html", context=context)


def add_resident_activity(request):
    condominium = get_condominium(request)
    user = CondominiumProfile.objects.get(pk=int(request.user.id))
    resident = Resident.objects.get(name=user.condominium_name, email=user.email)

    form = ResidentActivityForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            activity = ResidentActivity()
            activity.condominium = condominium
            activity.kind = form.cleaned_data['kind']
            activity.protocol = _create_code()
            activity.title = form.cleaned_data['title']
            activity.description = form.cleaned_data['description']
            activity.resident = user.condominium_name
            activity.apartment = resident.apartment
            activity.link = form.cleaned_data['link'] if form.cleaned_data['link'] else ""

            if request.FILES.get("image"):
                activity.image = request.FILES.get("image")

            activity.status = "ABERTA"
            activity.save()
            add_manager_notification(condominium,
                                     "NOVA ATIVIDADE DE MORADOR RECEBIDA. " + activity.title.upper())

            messages.success(request, "Atividade solicitada, o responsável será notificado, acompanhe o status pela sua"
                                      "aplicação!")

        return redirect(reverse('info:my-activities'))

    context = {'form': form,
               }
    return render(request, "info/condominium/apartment/add_activity.html", context=context)


@login_required(login_url='info:sign-in')
def edit_resident_activity(request, id):
    condominium = get_condominium(request)
    activity = get_object_or_404(ResidentActivity, pk=int(id), condominium=condominium)

    form = ResidentActivityForm(instance=activity)

    if request.method == "POST":
        form = ResidentActivityForm(request.POST or None)

        if form.is_valid():
            activity.kind = form.cleaned_data['kind'] or activity.kind
            activity.title = form.cleaned_data['title']
            activity.description = form.cleaned_data['description']
            activity.link = form.cleaned_data['link'] if form.cleaned_data['link'] else ""

            if request.FILES.get("image"):
                activity.image = request.FILES.get("image")

            activity.save()

            messages.success(request, "Atividade atualizada, o responsável será notificado, acompanhe o status pela sua"
                                      "aplicação!")

        return redirect(reverse('info:my-activities'))

    context = {'form': form,
               }
    return render(request, "info/condominium/apartment/edit_activity.html", context=context)


@login_required(login_url='info:sign-in')
def view_resident_activity(request, id):
    condominium = get_condominium(request)
    activity = get_object_or_404(ResidentActivity, pk=int(id), condominium=condominium)
    form = ViewResidentActivityForm(instance=activity)
    responses = ResidentActivityAnswer.objects.filter(activity=activity).order_by('-created')

    ResponseFormset = modelformset_factory(ResidentActivityAnswer, form=ViewResidentActivityAnswerForm, extra=0)
    formset = ResponseFormset(request.POST or None, queryset=responses, prefix="responses")

    AddResponseFormset = modelformset_factory(ResidentActivityAnswer, form=ResidentActivityAddAnswerForm, extra=0)
    queryset = ResidentActivityAnswer.objects.none()
    response_formset = AddResponseFormset(request.POST or None, queryset=queryset, prefix="response")

    if request.method == "POST":
        user = CondominiumProfile.objects.get(pk=request.user.id)

        if all([response_formset.is_valid()]):
            count = 0
            for added in response_formset:
                if added.has_changed():
                    response = ResidentActivityAnswer()
                    response.activity = activity
                    response.message = added.cleaned_data['message']
                    response.auteur = user.condominium_name
                    response.link = added.cleaned_data['link'] if added.cleaned_data['link'] else ""

                    response.image = request.FILES.get(f"response-{count}-image") if request.FILES.get(
                        f"response-{count}-image") else None
                    response.save()
                    if not user.resident_in:
                        activity.responsible = user.condominium_name
                        activity.status = "EM ANDAMENTO"
                        activity.save()
                        residents = Resident.objects.filter(apartment=activity.apartment)
                        to_list = []
                        for resident in residents:
                            to_list.append(resident.email)
                        add_notification(get_condominium(request), to_list,
                                         "Nova resposta adicionada a sua atividade " + activity.title.upper() +
                                         ". Acesse através do menu Atividades.", None, '/my-activities')
                    count = count + 1

            messages.success(request, "Resposta adicionadas, acompanhe o status pela sua"
                                      "aplicação!")

        return redirect(reverse('info:view-my-activity', args=[int(id)]))

    context = {'form': form,
               'formset': formset,
               'response_formset': response_formset,
               'status': activity.status,
               'activity': activity,
               'responses': responses
               }
    if len(responses):
        context['responses'] = responses
    return render(request, "info/condominium/apartment/view_activity.html", context=context)


@login_required(login_url='info:sign-in')
def finish_resident_activity(request, id):
    condominium = get_condominium(request)
    activity = get_object_or_404(ResidentActivity, pk=int(id), condominium=condominium)
    user = CondominiumProfile.objects.get(pk=int(request.user.id))
    activity.status = "ENCERRADA"
    if not user.resident_in:
        activity.responsible = user.condominium_name
        residents = Resident.objects.filter(apartment=activity.apartment)
        to_list = []
        for resident in residents:
            to_list.append(resident.email)
        add_notification(get_condominium(request), to_list,
                         "Atividade " + activity.title.upper() +
                         " finalizada por " + user.condominium_name + ". Acesse através do menu Atividades.", None, '/my-activities')
    activity.save()
    messages.success(request, "Atividade encerrada, o responsável será notificado")
    add_manager_notification(condominium,
                             "ATIVIDADE DE MORADOR ENCERRADA. " + activity.title.upper())

    if not user.resident_in:
        return redirect(reverse('info:resident-activities'))

    return redirect(reverse('info:my-activities'))


def _create_code():
    """This function generate 5 character long hash"""
    hash = hashlib.sha1()
    hash.update(str(time.time()).encode('utf-8'))
    return hash.hexdigest()[:6]


def get_server_time(request):
    current_time = datetime.datetime.now(FIXED_TZ).strftime('%H:%M:%S')
    return JsonResponse({'current_time': current_time})


def elapsed_time(request, id):
    current_time = datetime.datetime.now(FIXED_TZ).strftime('%H:%M:%S')
    return JsonResponse({'current_time': current_time})


@login_required(login_url='info:sign-in')
def aux_clean_plate(request):
    condominium = get_condominium(request)
    visitants = Visitant.objects.filter(condominium=condominium)
    for visitant in visitants:
        visitant.vehicle_plate = visitant.vehicle_plate.replace(' ', '').replace('-', '')
        visitant.save()

    return redirect(reverse('info:dashboard'))


def _exists_visitant(visitant):
    return Visitant.objects.filter(
        condominium=visitant.condominium,
        block=visitant.block,
        apartment=visitant.apartment,
        name=visitant.name,
        vehicle_plate=visitant.vehicle_plate,
        until=visitant.until,
        resident=visitant.resident,
        leaves_in__isnull=True
    ).exists()


def _vehicle_plate_active(condominium, vehicle_plate, exclude_pk=None):
    """Verifica se já existe um visitante ativo (sem saída registrada) com a mesma placa."""
    return bool(_get_active_visitants_by_plate(condominium, vehicle_plate, exclude_pk=exclude_pk))


@login_required(login_url='info:sign-in')
def remove_permanent_visitant(request):
    condominium = get_condominium(request)
    visitants = Visitant.objects.filter(condominium=condominium)

    for visitant in visitants:
        if visitant.until and visitant.until.date() == condominium.plan_expiration:
            visitant.delete()

    return redirect(reverse('info:dashboard'))


def remove_duplicate_visitant(request):

    # for condominium in CondominiumProfile.objects.all(resident_in__null=True, work_for__null=True):
        # duplicates = (
        #     Visitant.objects
        #     .values('vehicle_plate')
        #     .annotate(plate_count=Count('vehicle_plate'))
        #     .filter(plate_count__gt=1)
        # )

    latest_ids = (
        Visitant.objects
        .values('condominium', 'vehicle_plate')
        .annotate(latest_id=Max('id'))
        .values_list('latest_id', flat=True)
    )

    # Delete all that are NOT the newest
    Visitant.objects.exclude(id__in=list(latest_ids)).delete()
    messages.success(request, "Visitantes duplicados excluídos!")

    return redirect(reverse('info:dashboard'))
