from datetime import timedelta, date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from info.forms import AdministratorUserForm, UserForm
from info.models import CondominiumProfile, Notification, Review, HowTo, Block
from info.utils import send_verification_email, send_notification_email, get_condominium
from info.views import _def_user_adm_permissions, _def_user_all_permissions


def sign_up(request):
    form = AdministratorUserForm()
    if request.method == "POST":
        form = AdministratorUserForm(request.POST)

        if form.is_valid():
            email = str(request.POST.get("email")).lower()
            try:
                CondominiumProfile.objects.get(email=email)
                messages.error(request, "Email já cadastrado!, acesse sua conta ou entre em contato com nosso suporte")

            except CondominiumProfile.DoesNotExist:

                current_date = date.today()
                plan_expiration = current_date + timedelta(7)

                password = str(1234)
                user = CondominiumProfile()
                user.email = email
                user.set_password(password)
                user.address = request.POST.get("address") or ""
                user.liquidator_name = request.POST.get("liquidator_name") or ""
                user.admin_name = request.POST.get("admin_name") or ""
                user.whatsapp = request.POST.get("whatsapp") or ""
                user.site = request.POST.get("site") or ""
                user.cnpj = request.POST.get("cnpj") or ""
                user.plan_expiration = plan_expiration
                user.is_administrator = True
                user.save()


                _def_user_adm_permissions(user)

                send_verification_email(request, user)
                messages.success(request, "Cadastro realizado!, verifique seu email para ativar sua conta")
                send_notification_email(request, user)

                return redirect(reverse('info:sign-in'))
        else:
            print(form.errors)
    context = {'form': form}

    return render(request, "info/admininstrator/account/signup.html", context=context)


@login_required(login_url='info:sign-in')
def condominiuns(request):
    admin = CondominiumProfile.objects.get(pk=int(request.user.id))
    condominium_list = CondominiumProfile.objects.filter(managed_by=admin)

    search_name = request.GET.get('condominium_name')

    if search_name:
        condominium_list = condominium_list.filter(condominium_name__contains=search_name)

    context = {'condomíniums': condominium_list,
               }
    return render(request, "info/admininstrator/managing/codominiums.html", context=context)


@login_required(login_url='info:sign-in')
def dashboard(request, id):
    user = CondominiumProfile.objects.get(pk=id)

    notifications = Notification.objects.filter(receiver=user, read=False)
    show_review = Review.objects.filter(allowed_users=user).exists()
    # show_survey = SurveyModel.objects.filter(allowed_users=).exists()
    show_survey = True if len(user.survey_recipients.all()) else False
    show_bill = True if len(user.resident_user.all()) else False

    context = {
        'notifications': notifications, 'show_review': show_review, 'show_survey': show_survey,
        'show_bill': show_bill,
        'is_employee': True if user.work_for else False,
        'profile': user.profile,
        'user': user,
        'adm': True
    }

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

    return render(request, "info/dashboard.html", context=context)


@login_required(login_url='info:sign-in')
def select_condominium(request, id):
    admin = CondominiumProfile.objects.get(pk=int(request.user.id))
    user = CondominiumProfile.objects.get(pk=id)
    admin.selected = user.pk
    admin.save()
    return redirect(reverse('info:dashboard-condominium', args=[int(id)]))


@login_required(login_url='info:sign-in')
def delete_condominium(request, id):
    admin = CondominiumProfile.objects.get(pk=int(request.user.id))
    user = CondominiumProfile.objects.get(pk=id)
    user.delete()
    return redirect(reverse('info:admin-condominiums'))


@login_required(login_url='info:sign-in')
def back_admin(request):
    admin = CondominiumProfile.objects.get(pk=int(request.user.id))
    admin.selected = 0
    admin.save()
    return redirect(reverse('info:admin-condominiums'))


def add_condominium(request):
    admin = get_condominium(request)
    form = UserForm()
    if request.method == "POST":
        form = UserForm(request.POST)

        if form.is_valid():
            try:
                email = request.POST.get("email")
                CondominiumProfile.objects.get(email=email)
                messages.error(request,
                               "Condomínio já cadastrado!, acesse sua conta ou entre em contato com nosso suporte")

            except CondominiumProfile.DoesNotExist:

                plan_expiration = admin.plan_expiration

                error = False
                user_password = str(1234)
                email = str(request.POST.get("email")).lower()

                password = request.POST.get("new_password1")
                confirmation = request.POST.get("new_password2")

                try:
                    if len(password) != 4:
                        messages.error("A senha deve conter 4 dígitos")
                        error = True
                    elif int(password) == int(confirmation):
                        user_password = password
                except ValueError:
                    messages.error(request, "As senhas devem conter apenas números")
                    error = True

                if not error:

                    user = CondominiumProfile()
                    user.email = email
                    user.set_password(password)
                    user.condominium_name = request.POST.get("condominium_name")
                    user.address = request.POST.get("address") or ""
                    user.liquidator_name = request.POST.get("liquidator_name") or ""
                    user.admin_name = request.POST.get("admin_name") or ""
                    user.whatsapp = request.POST.get("whatsapp") or ""
                    user.site = request.POST.get("site") or ""
                    user.plan_expiration = plan_expiration
                    user.managed_by = admin
                    user.is_active = True
                    user.email_verified = True
                    user.save()

                    _def_user_all_permissions(user)
                    counter = 1
                    if request.POST.get("blocks"):
                        blocks = int(request.POST.get("blocks"))
                    else:
                        blocks = 1

                    for i in range(blocks):
                        block = Block()
                        block.name = "Bloco " + str(counter)
                        block.condominium = (user)
                        block.save()
                        counter += 1

                    send_verification_email(request, user)

                    messages.success(request, "Cadastro realizado!")

                    send_notification_email(request, user)

                    return redirect(reverse('info:admin-condominiums'))
        else:
            print(form.errors)
    context = {'form': form}

    return render(request, "info/admininstrator/account/add_condominium.html", context=context)
