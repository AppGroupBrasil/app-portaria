import hashlib
import json
import time
import smtplib
import pandas
import pytz
import os

from datetime import date, timedelta, time as dt_time, datetime
from tempfile import NamedTemporaryFile

from django.contrib.auth.models import Permission
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files import File
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.forms import model_to_dict
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic.base import TemplateView
from django.views.decorators.cache import never_cache
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from .forms import AuthForm, UserForm, ForgottenPasswordForm, UserEmailForm, ExcelUploadForm, UserProfileForm, \
    EditHowToForm, ConfigureMessagesForm, MessageBillForm
from .info_viwes.condominium.contract.contract_view import contracts
from .info_viwes.condominium.firebase.firebase_view import send_push_notification
from .info_viwes.condominium.whatsapp_api.whatsapp_view import send_info_message
from .models import CondominiumProfile, Block, Apartment, Resident, HowTo, Notification, Review, SurveyModel, \
    UserControl, ResidentFeatures, Visitant, Informative, Contract, ResidentActivity, Message, Checklist, \
    MessagesInformation, MessagesPayment, Order, Place, ReservationTime
from django.conf import settings

from .utils import send_verification_email, send_notification_email, get_user_from_email_verification_token, \
    EmailVerificationTokenGenerator, add_manager_notification, get_condominium

FIXED_TZ = pytz.timezone("America/Sao_Paulo")


# Create your views here.

class HomeView(TemplateView):
    template_name = "info/home.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse('info:dashboard'))

        return redirect(reverse('info:sign-in'))


def profiles(request):
    return render(request, "info/condominium/account/profiles.html")


def profile_detail(request, profile):
    details = []
    name = ""

    if profile == "security":
        details = ['Cadastro de unidades', 'Cadastro de moradores', 'Cadastro de funcionários', 'Correspondências',
                   'Controle de acesso veículos e pedestres', 'Interfonia', 'Relatórios']
        name = 'Portaria'

    context = {
        'details': details,
        'profile': profile,
        'name': name,
    }

    return render(request, "info/condominium/account/profile_detail.html", context=context)


def sign_up(request, profile):
    form = UserForm()
    if request.method == "POST":
        form = UserForm(request.POST)

        if form.is_valid():
            email = str(request.POST.get("email")).lower()
            try:
                CondominiumProfile.objects.get(email=email)
                messages.error(request,
                               "Condomínio já cadastrado!, acesse sua conta ou entre em contato com nosso suporte")
            except CondominiumProfile.DoesNotExist:

                current_date = date.today()
                plan_expiration = current_date + timedelta(365)

                user = CondominiumProfile()
                user.email = email
                user.condominium_name = request.POST.get("condominium_name")
                user.address = request.POST.get("address") or ""
                user.liquidator_name = request.POST.get("liquidator_name") or ""
                user.admin_name = request.POST.get("admin_name") or ""
                user.whatsapp = request.POST.get("whatsapp") or ""
                user.site = request.POST.get("site") or ""
                user.cnpj = request.POST.get("cnpj") or ""
                user.plan_expiration = plan_expiration

                password = request.POST.get("new_password1")
                confirmation = request.POST.get("new_password2")

                try:
                    if len(password) != 4:
                        form.add_error(None, "A senha deve conter 4 dígitos")
                        messages.error(request, "A senha deve conter 4 dígitos")
                    elif password == confirmation:
                        user.set_password(str(int(password)))
                        user.is_active = True
                        user.email_verified = True
                        user.save()

                        _def_user_security_permissions(user)

                        # send_verification_email(request, user)

                        messages.success(request, "Cadastro realizado!, verifique seu email para ativar sua conta")

                        send_notification_email(request, user)

                        _create_tests_instances(user)

                        return redirect(reverse('info:sign-in'))
                    else:
                        form.add_error(None, "As senhas não são iguais")
                        messages.error(request, "As senhas não são iguais")
                except ValueError:
                    form.add_error(None, "As senhas devem conter apenas números")
                    messages.error(request, "As senhas devem conter apenas números")
        else:
            print(form.errors)
    context = {'form': form}

    return render(request, "info/condominium/account/signup.html", context=context)


@never_cache
def sign_in(request):
    form = AuthForm()
    if request.method == "POST":

        form = AuthForm(data=request.POST)

        if form.is_valid():

            email = str(request.POST.get("email")).lower()
            password = request.POST.get("password")

            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)
                return redirect('info:dashboard')
            else:
                messages.error(request,
                               "Usuário não encontrado, faça seu registro, verifique a sua senha, ative sua conta ou entre em contato com o nosso suporte")

    context = {'form': form}

    return render(request, 'info/condominium/account/signin.html', context=context)


@login_required(login_url='info:sign-in')
def config_dashboard(request):
    user = CondominiumProfile.objects.get(pk=int(request.user.id))

    if request.method == "POST":
        user.use_tabs = request.POST.get("tabs") is not None and request.POST.get("tabs") == "on"
        user.save()

        messages.success(request, "Atualizado com sucesso!")

        return redirect(reverse('info:dashboard'))

    context = {'user': user,
               }
    return render(request, "info/condominium/account/config_dashboard.html", context=context)


@login_required(login_url='info:sign-in')
def config_residents(request):
    user = CondominiumProfile.objects.get(pk=int(request.user.id))

    if request.method == "POST":
        features = ResidentFeatures.objects.get(condominium=user)
        features.review = request.POST.get("review") is not None and request.POST.get("review") == "on"
        features.survey = request.POST.get("survey") is not None and request.POST.get("survey") == "on"
        features.bills = request.POST.get("bills") is not None and request.POST.get("bills") == "on"
        features.visitant = request.POST.get("visitant") is not None and request.POST.get("visitant") == "on"
        features.activity = request.POST.get("activity") is not None and request.POST.get("activity") == "on"
        features.booking = request.POST.get("booking") is not None and request.POST.get("booking") == "on"
        features.documents = request.POST.get("documents") is not None and request.POST.get("documents") == "on"
        features.permanent = request.POST.get("permanent") is not None and request.POST.get("permanent") == "on"
        if request.POST.get("visitant_switches") == "1":
            features.block_vehicle_inside = request.POST.get("block_vehicle_inside") == "on"
            features.auto_visitant_leave = request.POST.get("auto_visitant_leave") == "on"
        features.save()

        for resident in user.get_residents():
            _remove_resident_permission(resident)
            _add_resident_permission(resident)

        messages.success(request, "Configuração Atualizada com sucesso!")

        return redirect(reverse('info:dashboard'))

    try:
        features = ResidentFeatures.objects.get(condominium=user)
    except ResidentFeatures.DoesNotExist:
        features = ResidentFeatures()
        features.condominium = user
        features.save()

    context = {'user': user,
               'features': features,
               }
    return render(request, "info/condominium/account/resident_features.html", context=context)


@login_required(login_url='info:sign-in')
def dashboard(request):
    user = CondominiumProfile.objects.get(pk=request.user.id)

    adm = False
    if user.selected:
        user = CondominiumProfile.objects.get(pk=user.selected)
        adm = True

    notifications = Notification.objects.filter(receiver=user, read=False).order_by("-created")
    show_review = Review.objects.filter(allowed_users=user).exists()
    show_survey = True if len(user.survey_recipients.all()) else False
    show_bill = True if len(user.resident_user.all()) else False
    security = True if user.work_for or user.profile == 'intercom' else False
    condominium = get_condominium(request)
    dur_string = ""
    start_clock = None

    control = UserControl.objects.filter(condominium=condominium, user=user).order_by("-created").first()
    if control:
        if control.session_time:
            days, seconds = divmod(control.session_time.total_seconds(), 86400)
            hours, remainder = divmod(seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if days:
                dur_string = f"{int(days)} days, {int(hours):02}:{int(minutes):02}:{int(seconds):02}"
            else:
                dur_string = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
        else:
            start_clock = control.check_in.isoformat()

    context = {
        'notifications': notifications, 'show_review': show_review, 'show_survey': show_survey,
        'show_bill': show_bill,
        'is_employee': True if user.work_for else False,
        'profile': user.profile,
        'user': user,
        'security': security,
        'control': control,
        'session_time': dur_string,
        'start_clock': start_clock,
        'adm': adm
    }

    if notifications:
        last_not = notifications.first()

        send_push_notification(last_not.receiver, last_not.title, last_not.message,
                               last_not.url if last_not.url else None)

    how_to_create = HowTo.objects.get(name__exact="Dashboard > Cadastros")
    if how_to_create.kind == "Texto":
        context['how_to_create_text'] = how_to_create.value
    else:
        context['how_to_create_link'] = how_to_create.value

    how_to_manager = HowTo.objects.get(name__exact="Dashboard > Gestores")
    if how_to_manager.kind == "Texto":
        context['how_to_manager_text'] = how_to_manager.value
    else:
        context['how_to_manager_link'] = how_to_manager.value

    how_to_manager_resident = HowTo.objects.get(name__exact="Dashboard > Gestores com Moradores")
    if how_to_manager_resident.kind == "Texto":
        context['how_to_manager_resident_text'] = how_to_manager_resident.value
    else:
        context['how_to_manager_resident_link'] = how_to_manager_resident.value

    how_to_security = HowTo.objects.get(name__exact="Dashboard > Portaria com Moradores")
    if how_to_security.kind == "Texto":
        context['how_to_security_text'] = how_to_security.value
    else:
        context['how_to_security_link'] = how_to_security.value

    if user.use_tabs:
        return render(request, "info/tabs_dashboard.html", context=context)
    return render(request, "info/dashboard.html", context=context)


def read_notification(request):
    user = CondominiumProfile.objects.get(pk=request.user.id)
    notifications = Notification.objects.filter(receiver=user)
    pendings = notifications.filter(read=False)

    for notification in pendings:
        notification.read = True
        notification.save()

    return JsonResponse({"status": "OK"})


def sign_out(request):
    logout(request)
    return redirect(reverse('info:sign-in'))


class ForgottenPasswordView(TemplateView):
    template_name = "info/forgotten_password.html"


def email(request, condominium_name, email):
    try:
        send_mail(
            'Cadastro em Resolvido Info',
            'Olá ' + condominium_name + ' para criar a sua senha e ativar a sua conta click no link abaixo:',
            'resultadosintolerance@gmail.com',
            [email],
            fail_silently=False,
        )
    except smtplib.SMTPException:
        print("Erro aconteceu ao enviar email, cheque as configurações de acesso de segurança de sua conta de email")


def verification(request, uidb64, token):
    user = get_user_from_email_verification_token(self=uidb64, token=token)
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
                        if not user.added_by_link or user.resident_in.auto_approve:
                            user.is_active = True
                            message = "Senha criada com sucesso!, Acesse sua conta"
                        else:
                            add_manager_notification(user.resident_in,
                                                     "NOVO MORADOR CADASTRADO, faça a validação do cadastro na tela de moradores.")

                            message = "Senha criada com sucesso!, Você será notificado por email quando sua conta estiver ativa."
                        user.email_verified = True
                        user.save()
                        messages.success(request, message)
                        return redirect('info:sign-in')
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


def _create_hash():
    """This function generate 10 character long hash"""
    hash = hashlib.sha1()
    hash.update(str(time.time()).encode('utf-8'))
    return hash.hexdigest()[:-10]


def reset_password(request):
    form = UserEmailForm()

    if request.method == "POST":
        form = UserEmailForm(request.POST)

        if form.is_valid():
            try:
                email = request.POST.get("email")
                user = CondominiumProfile.objects.get(email=email)
                if not user.is_active:
                    form.add_error(None,
                                   "Usuário está bloqueado, entre em contato com o suporte para regularizar seu acesso!")
                else:
                    email_verification_token = EmailVerificationTokenGenerator()
                    current_site = get_current_site(request)

                    subject = 'Recuperação da sua conta Resolvido Info'
                    body = render_to_string(
                        'info/condominium/account/reset_password.html',
                        {
                            'domain': current_site.domain,
                            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                            'token': email_verification_token.make_token(user),
                        }
                    )

                    EmailMessage(to=[user.email], subject=subject, body=body).send()
                    text_content = strip_tags(body)
                    msg = EmailMultiAlternatives(to=[user.email], subject=subject, body=text_content)
                    msg.attach_alternative(body, "text/html")
                    msg.send()

                    messages.success(request, "Solicitação enviada!, verifique seu email para cadastrar uma nova senha")
                    return redirect(reverse('info:sign-in'))

            except CondominiumProfile.DoesNotExist:
                form.add_error(None, "Usuário ainda não cadastrado, verifique o email ou faça o seu cadastro")

    context = {'form': form}

    return render(request, "info/condominium/account/new_password.html", context=context)


@login_required(login_url='info:sign-in')
@staff_member_required
def add_from_file(request):
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

            file_path = handle_uploaded_file(excel_file)
            user = process_excel_data(file_path, email)
            _def_user_all_permissions(user)
            os.remove(file_path)

            send_verification_email(request, user)
            messages.success(request, "Cadastro realizado!, verifique seu email para ativar sua conta")

            return redirect(reverse('info:dashboard'))
    else:
        form = ExcelUploadForm()
    return render(request, 'info/admin/add_from_file.html', {'form': form})


def handle_uploaded_file(file):
    temp_file = NamedTemporaryFile(delete=False)
    file_path = temp_file.name
    with open(file_path, 'wb') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    return file_path


def process_excel_data(file_path, email):
    # Process the Excel file using pandas

    df = pandas.read_excel(file_path, header=None)
    df.dropna(axis=0, how='all', inplace=True)
    # Iterate through the rows of the DataFrame and create/save models
    # data = str(df.iloc[12][0])
    # print("## ",data, " ##")
    condominio_name = str(df.iloc[0][0])

    first_space_index = condominio_name.find(" ")
    condominio_name = condominio_name[first_space_index + 1:]

    condominium = CondominiumProfile()
    condominium.condominium_name = condominio_name
    condominium.email = email.lower()

    current_date = date.today()
    plan_expiration = current_date + timedelta(365)
    condominium.plan_expiration = plan_expiration
    condominium.set_password(str(1234))
    condominium.is_active = True
    condominium.email_verified = True

    condominium.save()

    last_block = None
    for index, row in df.iloc[:-1].iterrows():
        try:
            if index > 3:
                # Add Bloco
                apt_bloco = str(row[0])
                if apt_bloco == "nan":

                    if last_block:
                        bloco = last_block.name

                    else:
                        block = Block()
                        block.name = "BLOCO 01"
                        block.condominium = condominium
                        block.save()
                        last_block = block

                    apt_comp = str(row[6])
                    space_index = apt_comp.find(" ")
                    apt = apt_comp[:space_index]

                else:
                    space_index = apt_bloco.find(" ")
                    apt = apt_bloco[:space_index]
                    bloco = apt_bloco[space_index + 1:]

                try:
                    block = Block.objects.get(condominium=condominium, name=bloco)
                except Block.DoesNotExist:
                    block = Block()
                    block.name = bloco
                    block.condominium = condominium
                    block.save()
                    last_block = block

                # Add Apartment
                apartment = Apartment()
                apartment.block = block
                apartment.number = int(apt)
                apt_comp = str(row[6])
                space_index = apt_comp.find(" ")
                apartment.complement = apt_comp[space_index + 1:]

                apartment.save()

                resident = Resident()
                resident.apartment = apartment
                resident.name = str(row[1])
                resident.kind = str(row[2])
                resident.email = str(row[12])
                whatsapp = str(row[3])
                if whatsapp != "nan" and len(whatsapp) <= 15:
                    resident.whatsapp = whatsapp
                else:
                    resident.whatsapp = ""

                if resident.email == "nan":
                    resident.email = ""

                resident.save()
        except IndexError:
            print("Column index out of range for row:", index)

    return condominium


@login_required(login_url='info:sign-in')
@staff_member_required
def clients(request):
    clients_list = CondominiumProfile.objects.filter(is_staff=False)

    search_name = request.GET.get('condominium_name')
    search_ref = request.GET.get('condominium_ref')
    search_email = request.GET.get('condominium_email')
    search_status = request.GET.get('status_filter')

    if search_name:
        clients_list = clients_list.filter(condominium_name__contains=search_name)
    if search_ref:
        main = clients_list.filter(condominium_name__contains=search_ref)
        residents = clients_list.filter(resident_in__condominium_name__contains=search_ref).exclude(
            resident_in__isnull=True)
        workers = clients_list.filter(work_for__condominium_name__contains=search_ref).exclude(work_for__isnull=True)

        clients_list = main.union(residents, workers)

    if search_email:
        clients_list = clients_list.filter(email__contains=search_email)

    if search_status:
        if search_status == "True":
            clients_list = clients_list.filter(is_active=True)
        else:
            clients_list = clients_list.filter(is_active=False)

    paginator = Paginator(clients_list, 20)  # Show 20 visitants per page
    page_number = request.GET.get('page')  # Get the page number from the request
    page_obj = paginator.get_page(page_number)  # Get the page object

    clients = []
    for client in page_obj:

        client_obj = model_to_dict(client)

        if not client.work_for and not client.resident_in:
            try:
                messages_info = MessagesInformation.objects.get(condominium=client)
            except MessagesInformation.DoesNotExist:
                messages_info = MessagesInformation()
                messages_info.condominium = client
                messages_info.save()

            client_obj['used'] = messages_info.messages_used
            client_obj['limit'] = messages_info.messages_limit
        else:
            client_obj['used'] = "-"
            client_obj['limit'] = "-"
            if client_obj['resident_in']:
                client_obj['resident_in'] = CondominiumProfile.objects.get(pk=int(client_obj['resident_in'])).condominium_name
            else:
                client_obj['work_for'] = CondominiumProfile.objects.get(pk=int(client_obj['work_for'])).condominium_name

        clients.append(client_obj)

    context = {'clients': clients,
               'page_obj': page_obj
               }
    return render(request, "info/admin/clients.html", context=context)


@login_required(login_url='info:sign-in')
def view_profile(request, id):
    profile = get_object_or_404(CondominiumProfile, pk=id)

    str_days = request.GET.get('new_expiration')

    if str_days:
        days = int(str_days)
        profile.is_active = True
        profile.plan_expiration = date.today() + timedelta(days)
        profile.is_testing = False
        profile.save()

        messages.success(request, "Cadastro Desbloqueado!")
        return redirect(reverse('info:clients'))

    context = {'profile': profile}

    return render(request, 'info/admin/view_profile.html', context=context)


@login_required(login_url='info:sign-in')
@staff_member_required
def remove_profile(request, id):
    profile = get_object_or_404(CondominiumProfile, pk=id)
    profile.delete()
    messages.success(request, "Cliente Removido!")
    return redirect(reverse('info:clients'))


@login_required(login_url='info:sign-in')
def block_profile(request, id):
    profile = get_object_or_404(CondominiumProfile, pk=id)

    profile.is_active = False
    profile.plan_expiration = date.today()
    profile.save()

    messages.success(request, "Cadastro bloqueado!")
    return redirect(reverse('info:clients'))


@login_required(login_url='info:sign-in')
@staff_member_required
def hows_to(request):
    hows_to_list = HowTo.objects.all()
    context = {'hows_to': hows_to_list}
    return render(request, 'info/admin/hows-to.html', context=context)


@login_required(login_url='info:sign-in')
@staff_member_required
def edit_how_to(request, id):
    hows_to = HowTo.objects.get(pk=id)

    if hows_to:
        form = EditHowToForm(instance=hows_to)

    if request.method == 'POST':
        form = EditHowToForm(request.POST)

        if form.is_valid():
            hows_to.value = form.cleaned_data['value']
            hows_to.kind = form.cleaned_data['kind']
            hows_to.save()
            messages.success(request, "Ajuda atuializada!")
            return redirect(reverse('info:hows-to'))

    context = {'form': form}

    return render(request, 'info/admin/edit_how_to.html', context=context)


@login_required(login_url='info:sign-in')
def configure_profile(request, id):
    user = get_condominium(request)

    if user.is_staff or user.pk == id:
        condominium = CondominiumProfile.objects.get(pk=id)

        if request.method == 'POST':
            if request.POST.get("apartment") is not None and request.POST.get("apartment") == "on":
                content_type = ContentType.objects.get(app_label='info', model='apartment')
                permissions_to_add = Permission.objects.filter(content_type=content_type)

                for permission in permissions_to_add:
                    condominium.user_permissions.add(permission)

            else:
                content_type = ContentType.objects.get(app_label='info', model='apartment')
                permissions_to_remove = Permission.objects.filter(user=condominium, content_type=content_type)

                for permission in permissions_to_remove:
                    condominium.user_permissions.remove(permission)

            if request.POST.get("resident") is not None and request.POST.get("resident") == "on":
                content_type = ContentType.objects.get(app_label='info', model='resident')
                permissions_to_add = Permission.objects.filter(content_type=content_type)

                for permission in permissions_to_add:
                    condominium.user_permissions.add(permission)

                if request.POST.get("report") is not None and request.POST.get("report") == "on":
                    create_resident_report_permission = Permission.objects.get(codename="resident_report")
                    condominium.user_permissions.add(create_resident_report_permission)

            else:
                content_type = ContentType.objects.get(app_label='info', model='resident')
                permissions_to_remove = Permission.objects.filter(user=condominium, content_type=content_type)

                for permission in permissions_to_remove:
                    condominium.user_permissions.remove(permission)

                create_resident_report_permission = Permission.objects.get(codename="resident_report")
                condominium.user_permissions.remove(create_resident_report_permission)

            if request.POST.get("visitant") is not None and request.POST.get("visitant") == "on":
                content_type = ContentType.objects.get(app_label='info', model='visitant')
                permissions_to_add = Permission.objects.filter(content_type=content_type)

                for permission in permissions_to_add:
                    if (not permission.codename == "add_visitant"):
                        condominium.user_permissions.add(permission)

                if request.POST.get("report") is not None and request.POST.get("report") == "on":
                    visitant_report_permission = Permission.objects.get(codename="visitant_report")
                    condominium.user_permissions.add(visitant_report_permission)

            else:
                content_type = ContentType.objects.get(app_label='info', model='visitant')
                permissions_to_remove = Permission.objects.filter(user=condominium, content_type=content_type)

                for permission in permissions_to_remove:
                    condominium.user_permissions.remove(permission)

                visitant_report_permission = Permission.objects.get(codename="visitant_report")
                condominium.user_permissions.remove(visitant_report_permission)

            if request.POST.get("informative") is not None and request.POST.get("informative") == "on":
                content_type = ContentType.objects.get(app_label='info', model='informative')
                permissions_to_add = Permission.objects.filter(content_type=content_type)

                for permission in permissions_to_add:
                    condominium.user_permissions.add(permission)

                if request.POST.get("report") is not None and request.POST.get("report") == "on":
                    create_activity_report_permission = Permission.objects.get(codename="activity_report")
                    condominium.user_permissions.add(create_activity_report_permission)

            else:
                content_type = ContentType.objects.get(app_label='info', model='informative')
                permissions_to_remove = Permission.objects.filter(user=condominium, content_type=content_type)

                for permission in permissions_to_remove:
                    condominium.user_permissions.remove(permission)

                create_activity_report_permission = Permission.objects.get(codename="activity_report")
                condominium.user_permissions.remove(create_activity_report_permission)

            if request.POST.get("order") is not None and request.POST.get("order") == "on":
                content_type = ContentType.objects.get(app_label='info', model='order')
                permissions_to_add = Permission.objects.filter(content_type=content_type)

                for permission in permissions_to_add:
                    condominium.user_permissions.add(permission)

                if request.POST.get("report") is not None and request.POST.get("report") == "on":
                    create_order_report_permission = Permission.objects.get(codename="order_report")
                    condominium.user_permissions.add(create_order_report_permission)

            else:
                content_type = ContentType.objects.get(app_label='info', model='order')
                permissions_to_remove = Permission.objects.filter(user=condominium, content_type=content_type)

                for permission in permissions_to_remove:
                    condominium.user_permissions.remove(permission)

                create_order_report_permission = Permission.objects.get(codename="order_report")
                condominium.user_permissions.remove(create_order_report_permission)

            if request.POST.get("message") is not None and request.POST.get("message") == "on":
                content_type = ContentType.objects.get(app_label='info', model='message')
                permissions_to_add = Permission.objects.filter(content_type=content_type)

                for permission in permissions_to_add:
                    condominium.user_permissions.add(permission)

                if request.POST.get("report") is not None and request.POST.get("report") == "on":
                    create_message_report_permission = Permission.objects.get(codename="message_report")
                    condominium.user_permissions.add(create_message_report_permission)

            else:
                content_type = ContentType.objects.get(app_label='info', model='message')
                permissions_to_remove = Permission.objects.filter(user=condominium, content_type=content_type)

                for permission in permissions_to_remove:
                    condominium.user_permissions.remove(permission)

                create_message_report_permission = Permission.objects.get(codename="message_report")
                condominium.user_permissions.remove(create_message_report_permission)

            if request.POST.get("review") is not None and request.POST.get("review") == "on":
                content_type = ContentType.objects.get(app_label='info', model='review')
                permissions_to_add = Permission.objects.filter(content_type=content_type)

                for permission in permissions_to_add:
                    condominium.user_permissions.add(permission)

                if request.POST.get("report") is not None and request.POST.get("report") == "on":
                    create_review_report_permission = Permission.objects.get(codename="review_report")
                    condominium.user_permissions.add(create_review_report_permission)

            else:
                content_type = ContentType.objects.get(app_label='info', model='review')
                permissions_to_remove = Permission.objects.filter(user=condominium, content_type=content_type)

                for permission in permissions_to_remove:
                    condominium.user_permissions.remove(permission)

                create_review_report_permission = Permission.objects.get(codename="review_report")
                condominium.user_permissions.remove(create_review_report_permission)

            if request.POST.get("surveymodel") is not None and request.POST.get("surveymodel") == "on":
                content_type = ContentType.objects.get(app_label='info', model='surveymodel')
                permissions_to_add = Permission.objects.filter(content_type=content_type)

                for permission in permissions_to_add:
                    condominium.user_permissions.add(permission)

                if request.POST.get("report") is not None and request.POST.get("report") == "on":
                    create_survey_report_permission = Permission.objects.get(codename="survey_report")
                    condominium.user_permissions.add(create_survey_report_permission)

            else:
                content_type = ContentType.objects.get(app_label='info', model='surveymodel')
                permissions_to_remove = Permission.objects.filter(user=condominium, content_type=content_type)

                for permission in permissions_to_remove:
                    condominium.user_permissions.remove(permission)
                create_survey_report_permission = Permission.objects.get(codename="survey_report")
                condominium.user_permissions.remove(create_survey_report_permission)

            if request.POST.get("contract") is not None and request.POST.get("contract") == "on":
                content_type = ContentType.objects.get(app_label='info', model='contract')
                permissions_to_add = Permission.objects.filter(content_type=content_type)

                for permission in permissions_to_add:
                    condominium.user_permissions.add(permission)

                if request.POST.get("report") is not None and request.POST.get("report") == "on":
                    create_contract_report_permission = Permission.objects.get(codename="contract_report")
                    condominium.user_permissions.add(create_contract_report_permission)

            else:
                content_type = ContentType.objects.get(app_label='info', model='contract')
                permissions_to_remove = Permission.objects.filter(user=condominium, content_type=content_type)

                for permission in permissions_to_remove:
                    condominium.user_permissions.remove(permission)

                create_contract_report_permission = Permission.objects.get(codename="contract_report")
                condominium.user_permissions.remove(create_contract_report_permission)

            if request.POST.get("checklist") is not None and request.POST.get("checklist") == "on":
                content_type = ContentType.objects.get(app_label='info', model='checklist')
                permissions_to_add = Permission.objects.filter(content_type=content_type)

                for permission in permissions_to_add:
                    condominium.user_permissions.add(permission)

                if request.POST.get("report") is not None and request.POST.get("report") == "on":
                    create_checklist_report_permission = Permission.objects.get(codename="checklist_report")
                    condominium.user_permissions.add(create_checklist_report_permission)

            else:
                content_type = ContentType.objects.get(app_label='info', model='checklist')
                permissions_to_remove = Permission.objects.filter(user=condominium, content_type=content_type)

                for permission in permissions_to_remove:
                    condominium.user_permissions.remove(permission)

                create_checklist_report_permission = Permission.objects.get(codename="checklist_report")
                condominium.user_permissions.remove(create_checklist_report_permission)

            if request.POST.get("storage") is not None and request.POST.get("storage") == "on":
                content_type = ContentType.objects.get(app_label='info', model='storageentry')
                permissions_to_add = Permission.objects.filter(content_type=content_type)

                for permission in permissions_to_add:
                    condominium.user_permissions.add(permission)

                content_type = ContentType.objects.get(app_label='info', model='product')
                permissions_to_add = Permission.objects.filter(content_type=content_type)

                for permission in permissions_to_add:
                    condominium.user_permissions.add(permission)

            else:
                content_type = ContentType.objects.get(app_label='info', model='storageentry')
                permissions_to_remove = Permission.objects.filter(user=condominium, content_type=content_type)

                for permission in permissions_to_remove:
                    condominium.user_permissions.remove(permission)

                content_type = ContentType.objects.get(app_label='info', model='product')
                permissions_to_remove = Permission.objects.filter(user=condominium, content_type=content_type)

                for permission in permissions_to_remove:
                    condominium.user_permissions.remove(permission)

            if request.POST.get("employee") is not None and request.POST.get("employee") == "on":
                add_employee_permission = Permission.objects.get(codename="add_employee")
                change_employee_permission = Permission.objects.get(codename="change_employee")
                view_employee_permission = Permission.objects.get(codename="view_employee")
                delete_employee_permission = Permission.objects.get(codename="delete_employee")

                condominium.user_permissions.add(add_employee_permission)
                condominium.user_permissions.add(change_employee_permission)
                condominium.user_permissions.add(view_employee_permission)
                condominium.user_permissions.add(delete_employee_permission)

            else:
                add_employee_permission = Permission.objects.get(codename="add_employee")
                change_employee_permission = Permission.objects.get(codename="change_employee")
                view_employee_permission = Permission.objects.get(codename="view_employee")
                delete_employee_permission = Permission.objects.get(codename="delete_employee")

                condominium.user_permissions.remove(add_employee_permission)
                condominium.user_permissions.remove(change_employee_permission)
                condominium.user_permissions.remove(view_employee_permission)
                condominium.user_permissions.remove(delete_employee_permission)

            if request.POST.get("userlocation") is not None and request.POST.get("userlocation") == "on":
                content_type = ContentType.objects.get(app_label='info', model='userlocation')
                permissions_to_add = Permission.objects.filter(content_type=content_type)

                for permission in permissions_to_add:
                    condominium.user_permissions.add(permission)

                if request.POST.get("report") is not None and request.POST.get("report") == "on":
                    create_location_report_permission = Permission.objects.get(codename="location_report")
                    condominium.user_permissions.add(create_location_report_permission)

            else:
                content_type = ContentType.objects.get(app_label='info', model='userlocation')
                permissions_to_remove = Permission.objects.filter(user=condominium, content_type=content_type)

                for permission in permissions_to_remove:
                    condominium.user_permissions.remove(permission)

                create_location_report_permission = Permission.objects.get(codename="location_report")
                condominium.user_permissions.remove(create_location_report_permission)

            if request.POST.get("intercom") is not None and request.POST.get("intercom") == "on":
                contact_permission = Permission.objects.get(codename="contact_resident")
                condominium.user_permissions.add(contact_permission)

            else:
                contact_permission = Permission.objects.get(codename="contact_resident")
                condominium.user_permissions.remove(contact_permission)

            if request.POST.get("timeline") is not None and request.POST.get("timeline") == "on":
                content_type = ContentType.objects.get(app_label='info', model='timeline')
                timeline_permission = Permission.objects.filter(content_type=content_type)
                condominium.user_permissions.add(*timeline_permission)
            else:
                content_type = ContentType.objects.get(app_label='info', model='timeline')
                timeline_permission = Permission.objects.filter(content_type=content_type)
                condominium.user_permissions.remove(*timeline_permission)

            if request.POST.get("bills") is not None and request.POST.get("bills") == "on":
                content_type = ContentType.objects.get(app_label='info', model='bill')
                bill_permission = Permission.objects.filter(content_type=content_type)
                condominium.user_permissions.add(*bill_permission)
            else:
                content_type = ContentType.objects.get(app_label='info', model='bill')
                bill_permission = Permission.objects.filter(content_type=content_type)
                condominium.user_permissions.remove(*bill_permission)

            if request.POST.get("resendent_activity") is not None and request.POST.get("resendent_activity") == "on":
                content_type = ContentType.objects.get(app_label='info', model='residentactivity')
                resident_activity_permission = Permission.objects.filter(content_type=content_type)
                condominium.user_permissions.add(*resident_activity_permission)
                add_resident_activity_permission = Permission.objects.get(codename="my_activity")
                condominium.user_permissions.remove(add_resident_activity_permission)
                content_type = ContentType.objects.get(app_label='info', model='residentactivityanswer')
                resendent_activity_a_permission_permission = Permission.objects.filter(content_type=content_type)
                condominium.user_permissions.add(*resendent_activity_a_permission_permission)
            else:
                content_type = ContentType.objects.get(app_label='info', model='residentactivity')
                resident_activity_permission = Permission.objects.filter(content_type=content_type)
                condominium.user_permissions.remove(*resident_activity_permission)
                content_type = ContentType.objects.get(app_label='info', model='residentactivityanswer')
                resendent_activity_a_permission_permission = Permission.objects.filter(content_type=content_type)
                condominium.user_permissions.remove(*resendent_activity_a_permission_permission)

            if request.POST.get("booking") is not None and request.POST.get("booking") == "on":
                content_type = ContentType.objects.get(app_label='info', model='reservation')
                booking_permission = Permission.objects.filter(content_type=content_type)
                condominium.user_permissions.add(*booking_permission)
                add_resident_booking_permission = Permission.objects.get(codename="my_booking")
                condominium.user_permissions.remove(add_resident_booking_permission)
            else:
                content_type = ContentType.objects.get(app_label='info', model='reservation')
                booking_permission = Permission.objects.filter(content_type=content_type)
                condominium.user_permissions.remove(*booking_permission)

            if request.POST.get("documents") is not None and request.POST.get("documents") == "on":
                documents_permission = Permission.objects.get(codename="add_documents")
                condominium.user_permissions.add(documents_permission)
                resident_documents_permission = Permission.objects.get(codename="my_documents")
                condominium.user_permissions.remove(resident_documents_permission)
            else:
                documents_permission = Permission.objects.get(codename="add_documents")
                condominium.user_permissions.remove(documents_permission)
                resident_documents_permission = Permission.objects.get(codename="my_documents")
                condominium.user_permissions.remove(resident_documents_permission)

            if request.POST.get("whatsapp_not") is not None and request.POST.get("whatsapp_not") == "on":
                condominium.whatsapp_notification = True
            else:
                condominium.whatsapp_notification = False

            condominium.save()
            messages.success(request, "Usuário configurado!")
            if user.is_staff:
                return redirect(reverse('info:clients'))
            else:
                return redirect(reverse('info:dashboard'))

        context = {'user': condominium}

        return render(request, 'info/admin/configure_profile.html', context=context)
    else:
        messages.error(request, "Ação não permitida")
        return redirect(reverse('info:dashboard'))


@login_required(login_url='info:sign-in')
@staff_member_required
def confirm_reset_password(request, id):
    condominium = CondominiumProfile.objects.get(pk=id)
    condominium.set_password("1234")
    condominium.save()
    messages.success(request, "Senha resetada para 1234")
    return redirect(reverse('info:view-profile', args=[int(id)]))


@login_required(login_url='info:sign-in')
@staff_member_required
def condominium_reset_password(request, id):
    condominium = CondominiumProfile.objects.get(pk=id)
    context = {'profile': condominium}
    return render(request, 'info/admin/reset_password.html', context=context)


@login_required(login_url='info:sign-in')
@staff_member_required
def configure_messages(request, id):
    condominium = CondominiumProfile.objects.get(pk=id)
    messages_info = MessagesInformation.objects.get(condominium=condominium)
    form = ConfigureMessagesForm(request.POST or None, instance=messages_info)
    if request.POST:
        if form.is_valid():
            messages_info.messages_limit = form.cleaned_data['messages_limit']
            messages_info.price = form.cleaned_data['price']

            if request.POST.get("allow_bill") is not None and request.POST.get("allow_bill") == "on":
                messages_info.allow_charge = True
            else:
                messages_info.allow_charge = False

            messages_info.save()
            messages.success(request, "Mensagens atualizadas!")
            return redirect(reverse('info:clients'))

    context = {'profile': condominium, 'form': form, 'id': id, 'info': messages_info}
    return render(request, 'info/admin/configure_messages.html', context=context)


@login_required(login_url='info:sign-in')
def confirm_bill(request, previous, next):
    last_dot_index = previous.rfind('.')
    previous_page = previous[:last_dot_index]
    previous_id = previous[last_dot_index + 1:]
    last_dot_index = next.rfind('.')
    next_page = next[:last_dot_index]
    next_id = next[last_dot_index + 1:]

    current_site = get_current_site(request)

    condominium = CondominiumProfile.objects.get(pk=int(next_id))
    messages_info = MessagesInformation.objects.get(condominium=condominium)

    context = {'previous': previous_page + "/" + previous_id,
               'domain': current_site.domain,
               'next': next_page + "/" + next_id,
               'value': (
                                    messages_info.messages_used - messages_info.messages_limit) * messages_info.price if messages_info.messages_used > messages_info.messages_limit else 0.0
               }
    return render(request, "info/admin/confirm_bill.html", context=context)


@login_required(login_url='info:sign-in')
@staff_member_required
def bill_messages(request, id):
    condominium = CondominiumProfile.objects.get(pk=id)
    messages_info = MessagesInformation.objects.get(condominium=condominium)

    if messages_info.messages_used > messages_info.messages_limit:
        payment = MessagesPayment()
        payment.condominium = condominium
        payment.price = (messages_info.messages_used - messages_info.messages_limit) * messages_info.price
        payment.save()
        messages_info.messages_used = 0
        messages_info.save()

        messages.success(request, "Mensagens atualizadas!")
    else:
        messages.error(request, "Mensagens gatúitas ainda não utilizadas!")
    return redirect(reverse('info:clients'))


@login_required(login_url='info:sign-in')
@staff_member_required
def messages_bills(request):
    bills = MessagesPayment.objects.all()

    paginator = Paginator(bills, 15)  # Show 20 visitants per page
    page_number = request.GET.get('page')  # Get the page number from the request
    page_obj = paginator.get_page(page_number)

    context = {'bills': bills,
               'page_obj': page_obj
               }
    return render(request, "info/admin/messages_bills.html", context=context)


@login_required(login_url='info:sign-in')
@staff_member_required
def view_message_bill(request, id):
    bill = MessagesPayment.objects.get(pk=id)
    form = MessageBillForm(request.POST or None, request.FILES or None, instance=bill)

    if request.POST:

        bill.bill = request.FILES.get('bill') or bill.bill
        bill.payment = request.FILES.get('payment') or bill.payment

        if bill.payment:
            bill.payed = True

        bill.save()

        messages.success(request, "Cobrança atualizada!")
        return redirect(reverse('info:messages-bills'))

    context = {'bill': bill,
               'form': form
               }
    return render(request, "info/admin/view_message_bill.html", context=context)


@login_required(login_url='info:sign-in')
def delete_message_bill(request, id):
    bill = MessagesPayment.objects.get(pk=id)
    if bill:
        bill.delete()
        messages.success(request, "Cobrança Removida!")
    else:
        messages.error(request, "Cobrança não encontrada!")
    return redirect('info:messages-bills')


def _def_user_all_permissions(user):
    view_appartment_permission = Permission.objects.get(codename="view_apartment")
    add_appartment_permission = Permission.objects.get(codename="add_apartment")
    view_resident_permission = Permission.objects.get(codename="view_resident")
    create_resident_report_permission = Permission.objects.get(codename="resident_report")
    add_resident_permission = Permission.objects.get(codename="add_resident")
    change_resident_permission = Permission.objects.get(codename="change_resident")
    view_informative_permission = Permission.objects.get(codename="view_informative")
    add_informative_permission = Permission.objects.get(codename="add_informative")
    change_informative_permission = Permission.objects.get(codename="change_informative")
    delete_informative_permission = Permission.objects.get(codename="delete_informative")
    export_informative_permission = Permission.objects.get(codename="export_informative")
    add_order_permission = Permission.objects.get(codename="add_order")
    view_order_permission = Permission.objects.get(codename="view_order")
    change_order_permission = Permission.objects.get(codename="change_order")
    view_message_permission = Permission.objects.get(codename="view_message")
    add_message_permission = Permission.objects.get(codename="add_message")
    add_message_all_permission = Permission.objects.get(codename="add_message_all")
    add_message_block_permission = Permission.objects.get(codename="add_message_block")
    view_review_permission = Permission.objects.get(codename="view_review")
    add_review_permission = Permission.objects.get(codename="add_review")
    create_review_report_permission = Permission.objects.get(codename="review_report")
    view_survey_permission = Permission.objects.get(codename="view_surveymodel")
    add_survey_permission = Permission.objects.get(codename="add_surveymodel")
    create_survey_report_permission = Permission.objects.get(codename="survey_report")
    add_contract_permission = Permission.objects.get(codename="add_contract")
    view_contract_permission = Permission.objects.get(codename="view_contract")
    delete_contract_permission = Permission.objects.get(codename="delete_contract")
    change_contract_permission = Permission.objects.get(codename="change_contract")
    create_contract_report_permission = Permission.objects.get(codename="contract_report")
    view_checklist_permission = Permission.objects.get(codename="view_checklist")
    add_checklist_permission = Permission.objects.get(codename="add_checklist")
    change_task_permission = Permission.objects.get(codename="change_task")
    view_user_location_permission = Permission.objects.get(codename="view_userlocation")
    create_location_report_permission = Permission.objects.get(codename="location_report")

    add_employee_permission = Permission.objects.get(codename="add_employee")
    change_employee_permission = Permission.objects.get(codename="change_employee")
    view_employee_permission = Permission.objects.get(codename="view_employee")
    delete_employee_permission = Permission.objects.get(codename="delete_employee")
    create_activity_report_permission = Permission.objects.get(codename="activity_report")
    create_order_report_permission = Permission.objects.get(codename="order_report")
    create_message_report_permission = Permission.objects.get(codename="message_report")
    create_checklist_report_permission = Permission.objects.get(codename="checklist_report")
    contact_permission = Permission.objects.get(codename="contact_resident")
    change_visitant_permission = Permission.objects.get(codename="change_visitant")
    visitant_report_permission = Permission.objects.get(codename="visitant_report")
    send_bill_permission = Permission.objects.get(codename="send_bill")
    add_timeline_permission = Permission.objects.get(codename="add_timeline")
    view_timeline_permission = Permission.objects.get(codename="view_timeline")
    timeline_report_permission = Permission.objects.get(codename="timeline_report")
    resident_activity_permission = Permission.objects.get(codename="resident_activity")
    reservation_report_permission = Permission.objects.get(codename="reservation_report")
    booking_permission = Permission.objects.get(codename="add_reservation")
    session_report_permission = Permission.objects.get(codename="session_report")
    documents_permission = Permission.objects.get(codename="add_documents")
    product_permission = Permission.objects.get(codename="add_product")

    # adicionar permissões de relatórios

    user.user_permissions.add(view_appartment_permission)
    user.user_permissions.add(add_appartment_permission)
    user.user_permissions.add(view_resident_permission)
    user.user_permissions.add(add_resident_permission)
    user.user_permissions.add(change_resident_permission)
    user.user_permissions.add(view_informative_permission)
    user.user_permissions.add(add_informative_permission)
    user.user_permissions.add(change_informative_permission)
    user.user_permissions.add(delete_informative_permission)
    user.user_permissions.add(export_informative_permission)
    user.user_permissions.add(add_order_permission)
    user.user_permissions.add(change_order_permission)
    user.user_permissions.add(view_order_permission)
    user.user_permissions.add(view_review_permission)
    user.user_permissions.add(add_review_permission)
    user.user_permissions.add(view_survey_permission)
    user.user_permissions.add(add_survey_permission)
    user.user_permissions.add(add_contract_permission)
    user.user_permissions.add(view_contract_permission)
    user.user_permissions.add(delete_contract_permission)
    user.user_permissions.add(change_contract_permission)
    user.user_permissions.add(view_checklist_permission)
    user.user_permissions.add(add_checklist_permission)
    user.user_permissions.add(change_task_permission)
    user.user_permissions.add(view_user_location_permission)
    user.user_permissions.add(view_message_permission)
    user.user_permissions.add(add_message_permission)
    user.user_permissions.add(add_message_all_permission)
    user.user_permissions.add(add_message_block_permission)
    user.user_permissions.add(add_employee_permission)
    user.user_permissions.add(change_employee_permission)
    user.user_permissions.add(view_employee_permission)
    user.user_permissions.add(delete_employee_permission)
    user.user_permissions.add(create_activity_report_permission)
    user.user_permissions.add(create_order_report_permission)
    user.user_permissions.add(create_message_report_permission)
    user.user_permissions.add(create_checklist_report_permission)
    user.user_permissions.add(create_contract_report_permission)
    user.user_permissions.add(create_survey_report_permission)
    user.user_permissions.add(create_review_report_permission)
    user.user_permissions.add(create_resident_report_permission)
    user.user_permissions.add(create_location_report_permission)
    user.user_permissions.add(contact_permission)
    user.user_permissions.add(change_visitant_permission)
    user.user_permissions.add(visitant_report_permission)
    user.user_permissions.add(send_bill_permission)
    user.user_permissions.add(add_timeline_permission)
    user.user_permissions.add(view_timeline_permission)
    user.user_permissions.add(timeline_report_permission)
    user.user_permissions.add(resident_activity_permission)
    user.user_permissions.add(reservation_report_permission)
    user.user_permissions.add(booking_permission)
    user.user_permissions.add(session_report_permission)
    user.user_permissions.add(documents_permission)
    user.user_permissions.add(product_permission)
    user.profile = 'main'
    user.save()


def remove_resident_permission(request):
    users = CondominiumProfile.objects.all()

    for user in users:
        if not user.resident_in:
            my_review_permission = Permission.objects.get(codename="my_reviews")
            add_visitant_permission = Permission.objects.get(codename="add_visitant")
            user.user_permissions.remove(my_review_permission)
            user.user_permissions.remove(add_visitant_permission)


def add_user_resident_permission(request):
    users = CondominiumProfile.objects.all()

    for user in users:
        if user.resident_in:
            _add_resident_permission(user)
        else:
            _remove_resident_permission(user)

    messages.success(request, "Permissões concedidas!")
    return redirect(reverse('info:dashboard'))


def remove_user_resident_permission(request):
    users = CondominiumProfile.objects.all()

    for user in users:
        if user.resident_in:
            _remove_resident_permission(user)

    messages.success(request, "Permissões concedidas!")
    return redirect(reverse('info:dashboard'))


def _add_resident_permission(user):
    try:
        features = ResidentFeatures.objects.get(condominium=user.resident_in)
    except ResidentFeatures.DoesNotExist:
        features = ResidentFeatures()
        features.condominium = user.resident_in
        features.save()

    if features.review:
        my_review_permission = Permission.objects.get(codename="my_reviews")
        user.user_permissions.add(my_review_permission)

    if features.survey:
        my_survey_permission = Permission.objects.get(codename="my_surveys")
        user.user_permissions.add(my_survey_permission)

    if features.bills:
        my_bills_permission = Permission.objects.get(codename="my_bills")
        user.user_permissions.add(my_bills_permission)

    if features.visitant:
        add_visitant_permission = Permission.objects.get(codename="add_visitant")
        user.user_permissions.add(add_visitant_permission)

    if features.activity:
        my_activity_permission = Permission.objects.get(codename="my_activity")
        user.user_permissions.add(my_activity_permission)

    if features.booking:
        my_booking_permission = Permission.objects.get(codename="my_booking")
        user.user_permissions.add(my_booking_permission)

    if features.documents:
        my_documents_permission = Permission.objects.get(codename="my_documents")
        user.user_permissions.add(my_documents_permission)

    my_notifications_permission = Permission.objects.get(codename="my_notifications")
    user.user_permissions.remove(my_notifications_permission)

    my_orders_permission = Permission.objects.get(codename="view_order")
    user.user_permissions.add(my_orders_permission)


def _remove_resident_permission(user):
    my_review_permission = Permission.objects.get(codename="my_reviews")
    my_bills_permission = Permission.objects.get(codename="my_bills")
    add_visitant_permission = Permission.objects.get(codename="add_visitant")
    my_survey_permission = Permission.objects.get(codename="my_surveys")
    my_activity_permission = Permission.objects.get(codename="my_activity")
    my_booking_permission = Permission.objects.get(codename="my_booking")
    my_documents_permission = Permission.objects.get(codename="my_documents")
    my_orders_permission = Permission.objects.get(codename="view_order")
    user.user_permissions.remove(my_orders_permission)
    user.user_permissions.remove(my_review_permission)
    user.user_permissions.remove(add_visitant_permission)
    user.user_permissions.remove(my_survey_permission)
    user.user_permissions.remove(my_bills_permission)
    user.user_permissions.remove(my_activity_permission)
    user.user_permissions.remove(my_booking_permission)
    user.user_permissions.remove(my_documents_permission)


def add_condominium_permission(request):
    users = CondominiumProfile.objects.all()
    send_bill_permission = Permission.objects.get(codename="send_bill")
    add_timeline_permission = Permission.objects.get(codename="add_timeline")
    view_timeline_permission = Permission.objects.get(codename="view_timeline")
    timeline_report_permission = Permission.objects.get(codename="timeline_report")
    resident_activity_permission = Permission.objects.get(codename="resident_activity")
    booking_permission = Permission.objects.get(codename="add_reservation")
    reservation_report_permission = Permission.objects.get(codename="reservation_report")
    session_report_permission = Permission.objects.get(codename="session_report")
    documents_permission = Permission.objects.get(codename="add_documents")

    for user in users:
        if not user.resident_in and not user.work_for:
            if not user.profile:
                user.profile = "main"

                user.user_permissions.add(send_bill_permission)
                user.user_permissions.add(add_timeline_permission)
                user.user_permissions.add(view_timeline_permission)
                user.user_permissions.add(timeline_report_permission)
                user.user_permissions.add(resident_activity_permission)
                user.user_permissions.add(reservation_report_permission)
                user.user_permissions.add(booking_permission)
                user.user_permissions.add(session_report_permission)
                user.user_permissions.add(documents_permission)
            elif user.profile == 'main':

                user.user_permissions.add(send_bill_permission)
                user.user_permissions.add(add_timeline_permission)
                user.user_permissions.add(view_timeline_permission)
                user.user_permissions.add(timeline_report_permission)
                user.user_permissions.add(resident_activity_permission)
                user.user_permissions.add(booking_permission)
                user.user_permissions.add(session_report_permission)
                user.user_permissions.add(documents_permission)

            elif user.profile == 'inspect' or user.profile == 'maintenance':
                user.user_permissions.add(send_bill_permission)
                user.user_permissions.add(add_timeline_permission)
                user.user_permissions.add(view_timeline_permission)
                user.user_permissions.add(timeline_report_permission)
            elif user.profile == 'finance':
                user.user_permissions.add(send_bill_permission)

    messages.success(request, "Permissões concedidas!")
    return redirect(reverse('info:dashboard'))


def _def_user_security_permissions(user):
    view_appartment_permission = Permission.objects.get(codename="view_apartment")
    add_appartment_permission = Permission.objects.get(codename="add_apartment")
    view_resident_permission = Permission.objects.get(codename="view_resident")
    add_resident_permission = Permission.objects.get(codename="add_resident")
    change_resident_permission = Permission.objects.get(codename="change_resident")
    add_order_permission = Permission.objects.get(codename="add_order")
    view_order_permission = Permission.objects.get(codename="view_order")
    change_order_permission = Permission.objects.get(codename="change_order")
    add_employee_permission = Permission.objects.get(codename="add_employee")
    change_employee_permission = Permission.objects.get(codename="change_employee")
    view_employee_permission = Permission.objects.get(codename="view_employee")
    delete_employee_permission = Permission.objects.get(codename="delete_employee")
    contact_permission = Permission.objects.get(codename="contact_resident")
    change_visitant_permission = Permission.objects.get(codename="change_visitant")
    create_order_report_permission = Permission.objects.get(codename="order_report")
    create_resident_report_permission = Permission.objects.get(codename="resident_report")
    visitant_report_permission = Permission.objects.get(codename="visitant_report")

    user.user_permissions.add(view_appartment_permission)
    user.user_permissions.add(add_appartment_permission)
    user.user_permissions.add(view_resident_permission)
    user.user_permissions.add(add_resident_permission)
    user.user_permissions.add(change_resident_permission)
    user.user_permissions.add(add_order_permission)
    user.user_permissions.add(change_order_permission)
    user.user_permissions.add(view_order_permission)
    user.user_permissions.add(add_employee_permission)
    user.user_permissions.add(change_employee_permission)
    user.user_permissions.add(view_employee_permission)
    user.user_permissions.add(delete_employee_permission)
    user.user_permissions.add(contact_permission)
    user.user_permissions.add(change_visitant_permission)
    user.user_permissions.add(create_order_report_permission)
    user.user_permissions.add(create_resident_report_permission)
    user.user_permissions.add(visitant_report_permission)

    content_type = ContentType.objects.get(app_label='info', model='informative')
    permissions_to_add = Permission.objects.filter(content_type=content_type)
    create_activity_report_permission = Permission.objects.get(codename="activity_report")
    content_type = ContentType.objects.get(app_label='info', model='checklist')
    permissions_to_add_check = Permission.objects.filter(content_type=content_type)
    create_checklist_report_permission = Permission.objects.get(codename="checklist_report")
    content_type = ContentType.objects.get(app_label='info', model='storageentry')
    permissions_to_add_sto = Permission.objects.filter(content_type=content_type)
    content_type = ContentType.objects.get(app_label='info', model='product')
    permissions_to_add_prod = Permission.objects.filter(content_type=content_type)
    content_type = ContentType.objects.get(app_label='info', model='timeline')
    timeline_permission = Permission.objects.filter(content_type=content_type)
    content_type = ContentType.objects.get(app_label='info', model='message')
    permissions_to_add_mess = Permission.objects.filter(content_type=content_type)
    content_type = ContentType.objects.get(app_label='info', model='residentactivity')
    resident_activity_permission = Permission.objects.filter(content_type=content_type)
    add_resident_activity_permission = Permission.objects.get(codename="my_activity")
    content_type = ContentType.objects.get(app_label='info', model='residentactivityanswer')
    resendent_activity_a_permission_permission = Permission.objects.filter(content_type=content_type)

    user.user_permissions.add(create_activity_report_permission)
    user.user_permissions.add(create_checklist_report_permission)
    user.user_permissions.add(*timeline_permission)
    user.user_permissions.add(*permissions_to_add)
    user.user_permissions.add(*permissions_to_add_check)
    user.user_permissions.add(*permissions_to_add_sto)
    user.user_permissions.add(*permissions_to_add_prod)
    user.user_permissions.add(*permissions_to_add_mess)
    user.user_permissions.add(*resident_activity_permission)
    user.user_permissions.remove(add_resident_activity_permission)
    user.user_permissions.add(*resendent_activity_a_permission_permission)

    user.profile = 'security'
    user.save()


def _def_user_intercom_permissions(user):
    view_appartment_permission = Permission.objects.get(codename="view_apartment")
    add_appartment_permission = Permission.objects.get(codename="add_apartment")
    view_resident_permission = Permission.objects.get(codename="view_resident")
    add_resident_permission = Permission.objects.get(codename="add_resident")
    change_resident_permission = Permission.objects.get(codename="change_resident")
    add_employee_permission = Permission.objects.get(codename="add_employee")
    change_employee_permission = Permission.objects.get(codename="change_employee")
    view_employee_permission = Permission.objects.get(codename="view_employee")
    delete_employee_permission = Permission.objects.get(codename="delete_employee")
    contact_permission = Permission.objects.get(codename="contact_resident")

    user.user_permissions.add(view_appartment_permission)
    user.user_permissions.add(add_appartment_permission)
    user.user_permissions.add(view_resident_permission)
    user.user_permissions.add(add_resident_permission)
    user.user_permissions.add(change_resident_permission)
    user.user_permissions.add(add_employee_permission)
    user.user_permissions.add(change_employee_permission)
    user.user_permissions.add(view_employee_permission)
    user.user_permissions.add(delete_employee_permission)
    user.user_permissions.add(contact_permission)
    user.profile = 'intercom'
    user.save()


def _def_user_inspect_permissions(user):
    view_informative_permission = Permission.objects.get(codename="view_informative")
    add_informative_permission = Permission.objects.get(codename="add_informative")
    change_informative_permission = Permission.objects.get(codename="change_informative")
    delete_informative_permission = Permission.objects.get(codename="delete_informative")
    export_informative_permission = Permission.objects.get(codename="export_informative")
    view_review_permission = Permission.objects.get(codename="view_review")
    add_review_permission = Permission.objects.get(codename="add_review")
    create_review_report_permission = Permission.objects.get(codename="review_report")
    view_survey_permission = Permission.objects.get(codename="view_surveymodel")
    add_survey_permission = Permission.objects.get(codename="add_surveymodel")
    create_survey_report_permission = Permission.objects.get(codename="survey_report")
    view_checklist_permission = Permission.objects.get(codename="view_checklist")
    add_checklist_permission = Permission.objects.get(codename="add_checklist")
    change_task_permission = Permission.objects.get(codename="change_task")
    view_user_location_permission = Permission.objects.get(codename="view_userlocation")
    create_location_report_permission = Permission.objects.get(codename="location_report")
    add_employee_permission = Permission.objects.get(codename="add_employee")
    change_employee_permission = Permission.objects.get(codename="change_employee")
    view_employee_permission = Permission.objects.get(codename="view_employee")
    delete_employee_permission = Permission.objects.get(codename="delete_employee")
    add_timeline_permission = Permission.objects.get(codename="add_timeline")
    view_timeline_permission = Permission.objects.get(codename="view_timeline")
    timeline_report_permission = Permission.objects.get(codename="timeline_report")
    create_checklist_report_permission = Permission.objects.get(codename="checklist_report")
    create_activity_report_permission = Permission.objects.get(codename="activity_report")

    user.user_permissions.add(view_informative_permission)
    user.user_permissions.add(add_informative_permission)
    user.user_permissions.add(change_informative_permission)
    user.user_permissions.add(delete_informative_permission)
    user.user_permissions.add(export_informative_permission)
    user.user_permissions.add(view_review_permission)
    user.user_permissions.add(add_review_permission)
    user.user_permissions.add(view_survey_permission)
    user.user_permissions.add(add_survey_permission)
    user.user_permissions.add(view_checklist_permission)
    user.user_permissions.add(add_checklist_permission)
    user.user_permissions.add(change_task_permission)
    user.user_permissions.add(view_user_location_permission)
    user.user_permissions.add(add_employee_permission)
    user.user_permissions.add(change_employee_permission)
    user.user_permissions.add(view_employee_permission)
    user.user_permissions.add(delete_employee_permission)
    user.user_permissions.add(create_survey_report_permission)
    user.user_permissions.add(create_review_report_permission)
    user.user_permissions.add(create_location_report_permission)
    user.user_permissions.add(add_timeline_permission)
    user.user_permissions.add(view_timeline_permission)
    user.user_permissions.add(timeline_report_permission)
    user.user_permissions.add(create_checklist_report_permission)
    user.user_permissions.add(create_activity_report_permission)
    user.profile = 'inspect'
    user.save()


def _def_user_maintenance_permissions(user):
    view_informative_permission = Permission.objects.get(codename="view_informative")
    add_informative_permission = Permission.objects.get(codename="add_informative")
    change_informative_permission = Permission.objects.get(codename="change_informative")
    delete_informative_permission = Permission.objects.get(codename="delete_informative")
    export_informative_permission = Permission.objects.get(codename="export_informative")
    view_review_permission = Permission.objects.get(codename="view_review")
    add_review_permission = Permission.objects.get(codename="add_review")
    create_review_report_permission = Permission.objects.get(codename="review_report")
    view_survey_permission = Permission.objects.get(codename="view_surveymodel")
    add_survey_permission = Permission.objects.get(codename="add_surveymodel")
    create_survey_report_permission = Permission.objects.get(codename="survey_report")
    view_checklist_permission = Permission.objects.get(codename="view_checklist")
    add_checklist_permission = Permission.objects.get(codename="add_checklist")
    change_task_permission = Permission.objects.get(codename="change_task")
    view_user_location_permission = Permission.objects.get(codename="view_userlocation")
    create_location_report_permission = Permission.objects.get(codename="location_report")
    add_employee_permission = Permission.objects.get(codename="add_employee")
    change_employee_permission = Permission.objects.get(codename="change_employee")
    view_employee_permission = Permission.objects.get(codename="view_employee")
    delete_employee_permission = Permission.objects.get(codename="delete_employee")
    add_timeline_permission = Permission.objects.get(codename="add_timeline")
    view_timeline_permission = Permission.objects.get(codename="view_timeline")
    timeline_report_permission = Permission.objects.get(codename="timeline_report")

    user.user_permissions.add(view_informative_permission)
    user.user_permissions.add(add_informative_permission)
    user.user_permissions.add(change_informative_permission)
    user.user_permissions.add(delete_informative_permission)
    user.user_permissions.add(export_informative_permission)
    user.user_permissions.add(view_review_permission)
    user.user_permissions.add(add_review_permission)
    user.user_permissions.add(view_survey_permission)
    user.user_permissions.add(add_survey_permission)
    user.user_permissions.add(view_checklist_permission)
    user.user_permissions.add(add_checklist_permission)
    user.user_permissions.add(change_task_permission)
    user.user_permissions.add(view_user_location_permission)
    user.user_permissions.add(add_employee_permission)
    user.user_permissions.add(change_employee_permission)
    user.user_permissions.add(view_employee_permission)
    user.user_permissions.add(delete_employee_permission)
    user.user_permissions.add(create_survey_report_permission)
    user.user_permissions.add(create_review_report_permission)
    user.user_permissions.add(create_location_report_permission)
    user.user_permissions.add(add_timeline_permission)
    user.user_permissions.add(view_timeline_permission)
    user.user_permissions.add(timeline_report_permission)
    user.profile = 'maintenance'
    user.save()


def _def_user_finance_permissions(user):
    view_appartment_permission = Permission.objects.get(codename="view_apartment")
    add_appartment_permission = Permission.objects.get(codename="add_apartment")
    view_resident_permission = Permission.objects.get(codename="view_resident")
    add_resident_permission = Permission.objects.get(codename="add_resident")
    change_resident_permission = Permission.objects.get(codename="change_resident")
    send_bill_permission = Permission.objects.get(codename="send_bill")

    user.user_permissions.add(view_appartment_permission)
    user.user_permissions.add(add_appartment_permission)
    user.user_permissions.add(view_resident_permission)
    user.user_permissions.add(add_resident_permission)
    user.user_permissions.add(change_resident_permission)
    user.user_permissions.add(send_bill_permission)
    user.profile = 'finance'
    user.save()


def _def_user_adm_permissions(user):
    user.profile = 'adm'
    user.save()


def aux(request):
    # users = CondominiumProfile.objects.all()
    # add_param_changes = Permission.objects.get(codename="add_paramchanges")
    # for user in users:
    #     if user.profile == 'main':
    #         user.user_permissions.add(add_param_changes)
    #         user.save()
    visitants = Visitant.objects.all()
    for visitant in visitants:
        if not visitant.allowed:
            visitant.arrived = False
            visitant.save()

    return redirect(reverse('info:dashboard'))


def _def_monitor_permissions(user):
    view_informative_permission = Permission.objects.get(codename="view_informative")
    add_informative_permission = Permission.objects.get(codename="add_informative")
    change_informative_permission = Permission.objects.get(codename="change_informative")
    delete_informative_permission = Permission.objects.get(codename="delete_informative")
    export_informative_permission = Permission.objects.get(codename="export_informative")
    add_contract_permission = Permission.objects.get(codename="add_contract")
    view_contract_permission = Permission.objects.get(codename="view_contract")
    delete_contract_permission = Permission.objects.get(codename="delete_contract")
    change_contract_permission = Permission.objects.get(codename="change_contract")
    create_contract_report_permission = Permission.objects.get(codename="contract_report")
    view_checklist_permission = Permission.objects.get(codename="view_checklist")
    add_checklist_permission = Permission.objects.get(codename="add_checklist")
    change_task_permission = Permission.objects.get(codename="change_task")
    view_user_location_permission = Permission.objects.get(codename="view_userlocation")
    create_location_report_permission = Permission.objects.get(codename="location_report")
    add_employee_permission = Permission.objects.get(codename="add_employee")
    change_employee_permission = Permission.objects.get(codename="change_employee")
    view_employee_permission = Permission.objects.get(codename="view_employee")
    delete_employee_permission = Permission.objects.get(codename="delete_employee")
    create_activity_report_permission = Permission.objects.get(codename="activity_report")
    create_checklist_report_permission = Permission.objects.get(codename="checklist_report")
    add_timeline_permission = Permission.objects.get(codename="add_timeline")
    view_timeline_permission = Permission.objects.get(codename="view_timeline")
    timeline_report_permission = Permission.objects.get(codename="timeline_report")
    product_permission = Permission.objects.get(codename="add_product")
    storage_report_permission = Permission.objects.get(codename="storage_report")

    user.user_permissions.add(view_informative_permission)
    user.user_permissions.add(add_informative_permission)
    user.user_permissions.add(change_informative_permission)
    user.user_permissions.add(delete_informative_permission)
    user.user_permissions.add(export_informative_permission)
    user.user_permissions.add(add_contract_permission)
    user.user_permissions.add(view_contract_permission)
    user.user_permissions.add(delete_contract_permission)
    user.user_permissions.add(change_contract_permission)
    user.user_permissions.add(view_checklist_permission)
    user.user_permissions.add(add_checklist_permission)
    user.user_permissions.add(change_task_permission)
    user.user_permissions.add(view_user_location_permission)
    user.user_permissions.add(add_employee_permission)
    user.user_permissions.add(change_employee_permission)
    user.user_permissions.add(view_employee_permission)
    user.user_permissions.add(delete_employee_permission)
    user.user_permissions.add(create_activity_report_permission)
    user.user_permissions.add(create_checklist_report_permission)
    user.user_permissions.add(create_contract_report_permission)
    user.user_permissions.add(create_location_report_permission)
    user.user_permissions.add(add_timeline_permission)
    user.user_permissions.add(view_timeline_permission)
    user.user_permissions.add(timeline_report_permission)
    user.user_permissions.add(product_permission)
    user.user_permissions.add(storage_report_permission)
    user.profile = 'monitor'
    user.save()


def _def_survey_permissions(user):
    view_appartment_permission = Permission.objects.get(codename="view_apartment")
    add_appartment_permission = Permission.objects.get(codename="add_apartment")
    view_resident_permission = Permission.objects.get(codename="view_resident")
    create_resident_report_permission = Permission.objects.get(codename="resident_report")
    add_resident_permission = Permission.objects.get(codename="add_resident")
    change_resident_permission = Permission.objects.get(codename="change_resident")
    view_review_permission = Permission.objects.get(codename="view_review")
    add_review_permission = Permission.objects.get(codename="add_review")
    create_review_report_permission = Permission.objects.get(codename="review_report")
    view_survey_permission = Permission.objects.get(codename="view_surveymodel")
    add_survey_permission = Permission.objects.get(codename="add_surveymodel")
    create_survey_report_permission = Permission.objects.get(codename="survey_report")

    user.user_permissions.add(view_appartment_permission)
    user.user_permissions.add(add_appartment_permission)
    user.user_permissions.add(view_resident_permission)
    user.user_permissions.add(add_resident_permission)
    user.user_permissions.add(change_resident_permission)
    user.user_permissions.add(create_resident_report_permission)
    user.user_permissions.add(view_review_permission)
    user.user_permissions.add(add_review_permission)
    user.user_permissions.add(create_review_report_permission)
    user.user_permissions.add(view_survey_permission)
    user.user_permissions.add(add_survey_permission)
    user.user_permissions.add(create_survey_report_permission)

    user.profile = 'survey'
    user.save()


def _def_booking_permissions(user):
    view_appartment_permission = Permission.objects.get(codename="view_apartment")
    add_appartment_permission = Permission.objects.get(codename="add_apartment")
    view_resident_permission = Permission.objects.get(codename="view_resident")
    create_resident_report_permission = Permission.objects.get(codename="resident_report")
    add_resident_permission = Permission.objects.get(codename="add_resident")
    change_resident_permission = Permission.objects.get(codename="change_resident")
    send_bill_permission = Permission.objects.get(codename="send_bill")
    booking_permission = Permission.objects.get(codename="add_reservation")
    reservation_report_permission = Permission.objects.get(codename="reservation_report")

    user.user_permissions.add(view_appartment_permission)
    user.user_permissions.add(add_appartment_permission)
    user.user_permissions.add(view_resident_permission)
    user.user_permissions.add(add_resident_permission)
    user.user_permissions.add(change_resident_permission)
    user.user_permissions.add(create_resident_report_permission)
    user.user_permissions.add(send_bill_permission)
    user.user_permissions.add(booking_permission)
    user.user_permissions.add(reservation_report_permission)
    user.profile = 'booking'
    user.save()


def grant_permission_by_profile(request):
    for user in CondominiumProfile.objects.all():
        if not user.resident_in and not user.work_for:
            if user.profile == "main":
                _def_user_all_permissions(user)
            elif user.profile == "security":
                _def_user_security_permissions(user)
            elif user.profile == "intercom":
                _def_user_intercom_permissions(user)
            elif user.profile == "inspect":
                _def_user_inspect_permissions(user)
            elif user.profile == "maintenance":
                _def_user_maintenance_permissions(user)
            elif user.profile == "finance":
                _def_user_finance_permissions(user)
            elif user.profile == "adm":
                _def_user_adm_permissions(user)
            elif user.profile == "monitor":
                _def_monitor_permissions(user)
            elif user.profile == "survey":
                _def_survey_permissions(user)
            elif user.profile == "booking":
                _def_booking_permissions(user)
            elif not user.profile:
                user.profile = "main"
                user.save()
                _def_user_all_permissions(user)

    messages.success(request, "Permissões concedidas!")
    return redirect(reverse('info:dashboard'))


def policy(request):
    return render(request, "info/policy.html")


def import_permissions(json_file):
    with open(json_file, 'r') as file:
        permissions_data = json.load(file)

    for permission_data in permissions_data:
        # Check if permission with the same content_type and codename already exists
        if not Permission.objects.filter(content_type_id=permission_data['fields']['content_type'],
                                         codename=permission_data['fields']['codename']).exists():
            # Create the permission if it doesn't exist
            try:
                Permission.objects.create(
                    content_type_id=permission_data['fields']['content_type'],
                    codename=permission_data['fields']['codename'],
                    name=permission_data['fields']['name']
                )
            except IntegrityError:
                pass


def add_new_security_permissions(request):
    create_order_report_permission = Permission.objects.get(codename="order_report")
    create_resident_report_permission = Permission.objects.get(codename="resident_report")
    visitant_report_permission = Permission.objects.get(codename="visitant_report")

    for user in CondominiumProfile.objects.all():
        if user.profile == "security":
            user.user_permissions.add(create_order_report_permission)
            user.user_permissions.add(create_resident_report_permission)
            user.user_permissions.add(visitant_report_permission)

            user.save()
    return redirect(reverse('info:dashboard'))


def import_permission(request):
    ContentType.objects.all().delete()
    Permission.objects.all().delete()
    # import_permissions('permissions_with_contenttypes.json')
    return redirect(reverse('info:dashboard'))


def manifest(request):
    return render(request, 'info/portaria-manifest.json', content_type='application/json')


def add_new_inspect_permissions(request):
    create_checklist_report_permission = Permission.objects.get(codename="checklist_report")
    create_activity_report_permission = Permission.objects.get(codename="activity_report")

    for user in CondominiumProfile.objects.all():
        if user.profile == 'inspect':
            user.user_permissions.add(create_checklist_report_permission)
            user.user_permissions.add(create_activity_report_permission)

            user.save()

    return redirect(reverse('info:dashboard'))


def add_new_intercom_permissions(request):
    create_resident_report_permission = Permission.objects.get(codename="resident_report")

    for user in CondominiumProfile.objects.all():
        if user.profile == 'intercom':
            user.user_permissions.add(create_resident_report_permission)

            user.save()

    return redirect(reverse('info:dashboard'))


def add_new_permissions(request):
    my_order_permission = Permission.objects.get(codename="view_order")

    for user in CondominiumProfile.objects.filter(resident_in__isnull=False):
        user.user_permissions.add(my_order_permission)
        user.save()

    return redirect(reverse('info:dashboard'))


def update_expiration(request):
    current_date = date.today()
    plan_expiration = current_date + timedelta(365)

    for user in CondominiumProfile.objects.all():
        user.plan_expiration = plan_expiration
        user.save()

    return redirect(reverse('info:dashboard'))


def remove_helps(request):
    helps = HowTo.objects.all()

    for help in helps:
        help.delete()

    return redirect(reverse('info:dashboard'))


def remove_add_visitant_from_non_residents(request):
    users = CondominiumProfile.objects.all()
    add_resident_permission = Permission.objects.get(codename="add_resident")
    add_visitant_permission = Permission.objects.get(codename="add_visitant")
    for user in users:
        if not user.resident_in:
            user.user_permissions.add(add_resident_permission)
            user.user_permissions.remove(add_visitant_permission)
            user.save()

    return redirect(reverse('info:dashboard'))


def _create_tests_instances(condominium):
    return redirect(reverse('info:dashboard'))


def remove_booking_permission(request):
    users = CondominiumProfile.objects.all()
    content_type = ContentType.objects.get(app_label='info', model='reservation')
    booking_permission = Permission.objects.filter(content_type=content_type)

    for user in users:
        user.user_permissions.remove(*booking_permission)
        user.save()

    return redirect(reverse('info:dashboard'))


def add_new_security_perm(request):
    content_type = ContentType.objects.get(app_label='info', model='informative')
    permissions_to_add = Permission.objects.filter(content_type=content_type)
    create_activity_report_permission = Permission.objects.get(codename="activity_report")
    content_type = ContentType.objects.get(app_label='info', model='checklist')
    permissions_to_add_check = Permission.objects.filter(content_type=content_type)
    create_checklist_report_permission = Permission.objects.get(codename="checklist_report")
    content_type = ContentType.objects.get(app_label='info', model='storageentry')
    permissions_to_add_sto = Permission.objects.filter(content_type=content_type)
    content_type = ContentType.objects.get(app_label='info', model='product')
    permissions_to_add_prod = Permission.objects.filter(content_type=content_type)
    content_type = ContentType.objects.get(app_label='info', model='timeline')
    timeline_permission = Permission.objects.filter(content_type=content_type)
    content_type = ContentType.objects.get(app_label='info', model='message')
    permissions_to_add_mess = Permission.objects.filter(content_type=content_type)
    content_type = ContentType.objects.get(app_label='info', model='residentactivity')
    resident_activity_permission = Permission.objects.filter(content_type=content_type)
    add_resident_activity_permission = Permission.objects.get(codename="my_activity")
    content_type = ContentType.objects.get(app_label='info', model='residentactivityanswer')
    resendent_activity_a_permission_permission = Permission.objects.filter(content_type=content_type)

    for condominium in CondominiumProfile.objects.filter(profile="security"):
        condominium.user_permissions.add(create_activity_report_permission)
        condominium.user_permissions.add(create_checklist_report_permission)
        condominium.user_permissions.add(*timeline_permission)
        condominium.user_permissions.add(*permissions_to_add)
        condominium.user_permissions.add(*permissions_to_add_check)
        condominium.user_permissions.add(*permissions_to_add_sto)
        condominium.user_permissions.add(*permissions_to_add_prod)
        condominium.user_permissions.add(*permissions_to_add_mess)
        condominium.user_permissions.add(*resident_activity_permission)
        condominium.user_permissions.remove(add_resident_activity_permission)
        condominium.user_permissions.add(*resendent_activity_a_permission_permission)

        condominium.save()

    return redirect(reverse('info:dashboard'))


def add_visitants_into_residents(request):
    condominium = CondominiumProfile.objects.get(email="MONITORAMENTO.JMF@PTCSOLUTIONS.COM.BR")
    add_visitant_permission = Permission.objects.get(codename="add_visitant")
    for user in CondominiumProfile.objects.filter(resident_in=condominium):
        _remove_resident_permission(user)
        user.user_permissions.add(add_visitant_permission)
        user.save()

    return redirect(reverse('info:dashboard'))


def _create_default_places(request, condominium):
    if not Place.objects.filter(condominium=condominium):

        domain = get_current_site(request).domain
        selected_days = "monday,tuesday,wednesday,thursday,friday,saturday,sunday,"

        quadra_fut = Place()
        quadra_fut.condominium = condominium
        quadra_fut.name = "Quadra de futebol"
        quadra_fut.description = "Quadra Poli esportiva"
        quadra_fut.capacity = 20
        quadra_fut.maximum_unity_reservation_per_month = 40
        quadra_fut.maximum_resident_reservation_per_month = 40
        quadra_fut.maximum_unity_reservation_per_year = 400
        quadra_fut.maximum_resident_reservation_per_year = 400
        quadra_fut.auto_confirmation = True

        image_path = 'img/quadra.jpeg'

        if domain.find(".com") != -1:
            static_path = os.path.join(settings.STATIC_ROOT, image_path)
        else:
            static_path = os.path.join(settings.STATICFILES_DIRS[0], image_path)

        with open(static_path, 'rb') as f:
            quadra_fut.image.save('quadra.jpeg', File(f), save=True)

        quadra_fut.allow_new_reservation = 5
        quadra_fut.save()

        init_time = dt_time(8, 0)
        until = dt_time(22, 0)
        interval = 1

        while until > init_time:

            init_datetime = datetime.combine(datetime.now(FIXED_TZ).date(), init_time)
            end_time = init_datetime + timedelta(hours=int(interval))

            if end_time.time() > until:
                end_time = until

            quadra_fut_time = ReservationTime()
            quadra_fut_time.condominium = condominium
            quadra_fut_time.init_time = init_datetime.time()
            quadra_fut_time.end_time = end_time.time()
            quadra_fut_time.day = selected_days
            quadra_fut_time.blocked = False
            quadra_fut_time.place = quadra_fut
            quadra_fut_time.save()

            init_time = end_time.time()

        churras = Place()
        churras.condominium = condominium
        churras.name = "Churrasqueira"
        churras.description = "Área da churrasqueira"
        churras.capacity = 20
        churras.maximum_unity_reservation_per_month = 40
        churras.maximum_resident_reservation_per_month = 40
        churras.maximum_unity_reservation_per_year = 400
        churras.maximum_resident_reservation_per_year = 400
        churras.auto_confirmation = True

        churras_image_path = 'img/churras.jpeg'

        if domain.find(".com") != -1:
            static_path = os.path.join(settings.STATIC_ROOT, churras_image_path)
        else:
            static_path = os.path.join(settings.STATICFILES_DIRS[0], churras_image_path)

        with open(static_path, 'rb') as f:
            churras.image.save('churras.jpeg', File(f), save=True)

        churras.allow_new_reservation = 2
        churras.save()

        init_time = dt_time(10, 0)
        until = dt_time(22, 0)
        interval = 12

        while until > init_time:

            init_datetime = datetime.combine(datetime.now(FIXED_TZ).date(), init_time)
            end_time = init_datetime + timedelta(hours=int(interval))

            if end_time.time() > until:
                end_time = until

            churras_time = ReservationTime()
            churras_time.condominium = condominium
            churras_time.init_time = init_datetime.time()
            churras_time.end_time = end_time.time()
            churras_time.day = selected_days
            churras_time.blocked = False
            churras_time.place = churras
            churras_time.save()

            init_time = end_time.time()

        festas = Place()
        festas.condominium = condominium
        festas.name = "Salão de Festas"
        festas.description = "Salão de festas completo com mesas e cadeiras"
        festas.capacity = 100
        festas.maximum_unity_reservation_per_month = 40
        festas.maximum_resident_reservation_per_month = 40
        festas.maximum_unity_reservation_per_year = 400
        festas.maximum_resident_reservation_per_year = 400
        festas.auto_confirmation = True

        festas_image_path = 'img/festas.jpeg'

        if domain.find(".com") != -1:
            static_path = os.path.join(settings.STATIC_ROOT, festas_image_path)
        else:
            static_path = os.path.join(settings.STATICFILES_DIRS[0], festas_image_path)

        with open(static_path, 'rb') as f:
            festas.image.save('festas.jpeg', File(f), save=True)

        festas.allow_new_reservation = 2
        festas.save()

        initial = init_time = dt_time(10, 0)
        until = dt_time(22, 0)
        interval = 12

        while until > init_time:

            init_datetime = datetime.combine(datetime.now(FIXED_TZ).date(), init_time)
            end_time = init_datetime + timedelta(hours=int(interval))

            if end_time.time() > until:
                end_time = until

            festas_time = ReservationTime()
            festas_time.condominium = condominium
            festas_time.init_time = init_datetime.time()
            festas_time.end_time = end_time.time()
            festas_time.day = selected_days
            festas_time.blocked = False
            festas_time.place = festas
            festas_time.save()

            init_time = end_time.time()


def test_new(request):
    condominium = get_condominium(request)
    _create_default_places(request, condominium)

    return redirect(reverse('info:dashboard'))

def add_residents_notification(request):

    for user in CondominiumProfile.objects.filter(resident_in__isnull=False):
        my_notifications_permission = Permission.objects.get(codename="my_notifications")
        user.user_permissions.add(my_notifications_permission)
        user.save()
    return redirect(reverse('info:dashboard'))
