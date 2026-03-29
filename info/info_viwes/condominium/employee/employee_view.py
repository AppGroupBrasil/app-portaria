from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Permission
from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.urls import reverse

from info.forms import AddEmployeeForm
from info.models import CondominiumProfile, ResidentFeatures
from info.utils import send_verification_email, get_condominium


@login_required(login_url='info:sign-in')
def employees(request):

    condominium = get_condominium(request)
    employee_list = condominium.get_employees()

    context = {'employees': employee_list,
               'user': condominium
               }
    return render(request, "info/condominium/employee/employees.html", context=context)


@login_required(login_url='info:sign-in')
def add_employee(request):

    condominium = CondominiumProfile.objects.get(pk=int(request.user.id))

    if request.method == "POST":

        # apartment = Con.objects.get(pk=int(request.POST.get('apartment')))
        form = AddEmployeeForm(request.POST)
        if form.is_valid():
            try:
                error = False
                if request.POST.get("default_pass") is not None and request.POST.get("default_pass") == "on":
                    password = request.POST.get("new_password1")
                    confirmation = request.POST.get("new_password2")

                    try:
                        if len(password) != 4:
                            messages.error("A senha deve conter 4 dígitos")
                            error = True
                        elif int(password) == int(confirmation):
                            employee = CondominiumProfile()
                            employee.condominium_name = form.cleaned_data['employee_name']
                            employee.email = str(form.cleaned_data['email']).lower()
                            employee.work_for = condominium
                            employee.plan_expiration = condominium.plan_expiration
                            employee.set_password(password)
                            employee.is_active = True
                            employee.email_verified = True
                            employee.added_by_link = False
                            employee.save()
                        else:
                            messages.error(request, "As senhas não são iguais")
                            error = True
                    except ValueError:
                        messages.error(request, "As senhas devem conter apenas números")
                        error = True
                else:
                    employee = CondominiumProfile()
                    employee.condominium_name = form.cleaned_data['employee_name']
                    employee.email = str(form.cleaned_data['email']).lower()
                    employee.work_for = condominium
                    employee.plan_expiration = condominium.plan_expiration
                    employee.email_verified = True
                    employee.is_active = True
                    employee.save()
                    send_verification_email(request, employee)

                if not error:
                    if request.POST.get("view_apartment") is not None and request.POST.get("view_apartment") == "on":
                        view_appartment_permission = Permission.objects.get(codename="view_apartment")
                        employee.user_permissions.add(view_appartment_permission)

                    if request.POST.get("add_apartment") is not None and request.POST.get("add_apartment") == "on":
                        add_appartment_permission = Permission.objects.get(codename="add_apartment")
                        employee.user_permissions.add(add_appartment_permission)

                    if request.POST.get("view_resident") is not None and request.POST.get("view_resident") == "on":
                        view_resident_permission = Permission.objects.get(codename="view_resident")
                        employee.user_permissions.add(view_resident_permission)

                    if request.POST.get("add_resident") is not None and request.POST.get("add_resident") == "on":
                        add_resident_permission = Permission.objects.get(codename="add_resident")
                        employee.user_permissions.add(add_resident_permission)

                    if request.POST.get("change_resident") is not None and request.POST.get("change_resident") == "on":
                        change_resident_permission = Permission.objects.get(codename="change_resident")
                        employee.user_permissions.add(change_resident_permission)

                    if request.POST.get("contact_resident") is not None and request.POST.get("contact_resident") == "on":
                        contact_resident_permission = Permission.objects.get(codename="contact_resident")
                        employee.user_permissions.add(contact_resident_permission)

                    if request.POST.get("change_visitant") is not None and request.POST.get("change_visitant") == "on":
                        change_visitant_permission = Permission.objects.get(codename="change_visitant")
                        employee.user_permissions.add(change_visitant_permission)

                    if request.POST.get("view_informative") is not None and request.POST.get("view_informative") == "on":
                        view_informative_permission = Permission.objects.get(codename="view_informative")
                        employee.user_permissions.add(view_informative_permission)

                    if request.POST.get("add_informative") is not None and request.POST.get("add_informative") == "on":
                        add_informative_permission = Permission.objects.get(codename="add_informative")
                        employee.user_permissions.add(add_informative_permission)

                    if request.POST.get("change_informative") is not None and request.POST.get("change_informative") == "on":
                        change_informative_permission = Permission.objects.get(codename="change_informative")
                        employee.user_permissions.add(change_informative_permission)

                    if request.POST.get("delete_informative") is not None and request.POST.get("delete_informative") == "on":
                        delete_informative_permission = Permission.objects.get(codename="delete_informative")
                        employee.user_permissions.add(delete_informative_permission)

                    if request.POST.get("export_informative") is not None and request.POST.get("export_informative") == "on":
                        export_informative_permission = Permission.objects.get(codename="export_informative")
                        employee.user_permissions.add(export_informative_permission)

                    if request.POST.get("view_order") is not None and request.POST.get("view_order") == "on":
                        view_order_permission = Permission.objects.get(codename="view_order")
                        employee.user_permissions.add(view_order_permission)

                    if request.POST.get("add_order") is not None and request.POST.get("add_order") == "on":
                        add_order_permission = Permission.objects.get(codename="add_order")
                        employee.user_permissions.add(add_order_permission)

                    if request.POST.get("change_order") is not None and request.POST.get("change_order") == "on":
                        change_order_permission = Permission.objects.get(codename="change_order")
                        employee.user_permissions.add(change_order_permission)

                    if request.POST.get("view_message") is not None and request.POST.get("view_message") == "on":
                        view_message_permission = Permission.objects.get(codename="view_message")
                        employee.user_permissions.add(view_message_permission)

                    if request.POST.get("add_message") is not None and request.POST.get("add_message") == "on":
                        add_message_permission = Permission.objects.get(codename="add_message")
                        employee.user_permissions.add(add_message_permission)

                    if request.POST.get("add_message_block") is not None and request.POST.get("add_message_block") == "on":
                        add_message_block_permission = Permission.objects.get(codename="add_message_block")
                        employee.user_permissions.add(add_message_block_permission)

                    if request.POST.get("add_message_all") is not None and request.POST.get("add_message_all") == "on":
                        add_message_all_permission = Permission.objects.get(codename="add_message_all")
                        employee.user_permissions.add(add_message_all_permission)

                    if request.POST.get("view_review") is not None and request.POST.get("view_review") == "on":
                        view_review_permission = Permission.objects.get(codename="view_review")
                        employee.user_permissions.add(view_review_permission)

                    if request.POST.get("add_review") is not None and request.POST.get("add_review") == "on":
                        add_review_permission = Permission.objects.get(codename="add_review")
                        employee.user_permissions.add(add_review_permission)

                    if request.POST.get("view_surveymodel") is not None and request.POST.get("view_surveymodel") == "on":
                        view_surveymodel_permission = Permission.objects.get(codename="view_surveymodel")
                        employee.user_permissions.add(view_surveymodel_permission)

                    if request.POST.get("add_surveymodel") is not None and request.POST.get("add_surveymodel") == "on":
                        add_surveymodel_permission = Permission.objects.get(codename="add_surveymodel")
                        employee.user_permissions.add(add_surveymodel_permission)

                    if request.POST.get("add_contract") is not None and request.POST.get("add_contract") == "on":
                        add_contract_permission = Permission.objects.get(codename="add_contract")
                        employee.user_permissions.add(add_contract_permission)

                    if request.POST.get("view_contract") is not None and request.POST.get("view_contract") == "on":
                        view_contract_permission = Permission.objects.get(codename="view_contract")
                        employee.user_permissions.add(view_contract_permission)

                    if request.POST.get("delete_contract") is not None and request.POST.get("delete_contract") == "on":
                        delete_contract_permission = Permission.objects.get(codename="delete_contract")
                        employee.user_permissions.add(delete_contract_permission)

                    if request.POST.get("change_contract") is not None and request.POST.get("change_contract") == "on":
                        change_contract_permission = Permission.objects.get(codename="change_contract")
                        employee.user_permissions.add(change_contract_permission)

                    if request.POST.get("view_checklist") is not None and request.POST.get("view_checklist") == "on":
                        view_checklist_permission = Permission.objects.get(codename="view_checklist")
                        change_task_permission = Permission.objects.get(codename="change_task")
                        employee.user_permissions.add(view_checklist_permission)
                        employee.user_permissions.add(change_task_permission)

                    if request.POST.get("add_checklist") is not None and request.POST.get("add_checklist") == "on":
                        add_checklist_permission = Permission.objects.get(codename="add_checklist")
                        employee.user_permissions.add(add_checklist_permission)

                    if request.POST.get("view_userlocation") is not None and request.POST.get("view_userlocation") == "on":
                        view_userlocation_permission = Permission.objects.get(codename="view_userlocation")
                        employee.user_permissions.add(view_userlocation_permission)

                    if request.POST.get("activity_report") is not None and request.POST.get("activity_report") == "on":
                        activity_report_permission = Permission.objects.get(codename="activity_report")
                        employee.user_permissions.add(activity_report_permission)

                    if request.POST.get("order_report") is not None and request.POST.get("order_report") == "on":
                        order_report_permission = Permission.objects.get(codename="order_report")
                        employee.user_permissions.add(order_report_permission)

                    if request.POST.get("message_report") is not None and request.POST.get("message_report") == "on":
                        message_report_permission = Permission.objects.get(codename="message_report")
                        employee.user_permissions.add(message_report_permission)

                    if request.POST.get("checklist_report") is not None and request.POST.get("checklist_report") == "on":
                        checklist_report_permission = Permission.objects.get(codename="checklist_report")
                        employee.user_permissions.add(checklist_report_permission)

                    if request.POST.get("contract_report") is not None and request.POST.get("contract_report") == "on":
                        contract_report_permission = Permission.objects.get(codename="contract_report")
                        employee.user_permissions.add(contract_report_permission)

                    if request.POST.get("survey_report") is not None and request.POST.get("survey_report") == "on":
                        survey_report_permission = Permission.objects.get(codename="survey_report")
                        employee.user_permissions.add(survey_report_permission)

                    if request.POST.get("review_report") is not None and request.POST.get("review_report") == "on":
                        review_report_permission = Permission.objects.get(codename="review_report")
                        employee.user_permissions.add(review_report_permission)

                    if request.POST.get("resident_report") is not None and request.POST.get("resident_report") == "on":
                        resident_report_permission = Permission.objects.get(codename="resident_report")
                        employee.user_permissions.add(resident_report_permission)

                    if request.POST.get("location_report") is not None and request.POST.get("location_report") == "on":
                        location_report_permission = Permission.objects.get(codename="location_report")
                        employee.user_permissions.add(location_report_permission)

                    if request.POST.get("visitant_report") is not None and request.POST.get("visitant_report") == "on":
                        visitant_report_permission = Permission.objects.get(codename="visitant_report")
                        employee.user_permissions.add(visitant_report_permission)

                    if request.POST.get("add_product") is not None and request.POST.get("add_product") == "on":
                        add_product_permission = Permission.objects.get(codename="add_product")
                        employee.user_permissions.add(add_product_permission)

                    if request.POST.get("add_storageentry") is not None and request.POST.get("add_storageentry") == "on":
                        add_storageentry_permission = Permission.objects.get(codename="add_storageentry")
                        employee.user_permissions.add(add_storageentry_permission)

                    if request.POST.get("storage_report") is not None and request.POST.get("storage_report") == "on":
                        storage_report_permission = Permission.objects.get(codename="storage_report")
                        employee.user_permissions.add(storage_report_permission)

                    if request.POST.get("add_timeline") is not None and request.POST.get("add_timeline") == "on":
                        add_timeline_permission = Permission.objects.get(codename="add_timeline")
                        employee.user_permissions.add(add_timeline_permission)

                    if request.POST.get("view_timeline") is not None and request.POST.get("view_timeline") == "on":
                        view_timeline_permission = Permission.objects.get(codename="view_timeline")
                        employee.user_permissions.add(view_timeline_permission)

                    if request.POST.get("timeline_report") is not None and request.POST.get("timeline_report") == "on":
                        timeline_report_permission = Permission.objects.get(codename="timeline_report")
                        employee.user_permissions.add(timeline_report_permission)

                    if request.POST.get("add_bill") is not None and request.POST.get("add_bill") == "on":
                        add_bill_permission = Permission.objects.get(codename="add_bill")
                        change_bill_permission = Permission.objects.get(codename="change_bill")
                        employee.user_permissions.add(add_bill_permission)
                        employee.user_permissions.add(change_bill_permission)

                    if request.POST.get("view_bill") is not None and request.POST.get("view_bill") == "on":
                        view_bill_permission = Permission.objects.get(codename="view_bill")
                        employee.user_permissions.add(view_bill_permission)

                    if request.POST.get("delete_bill") is not None and request.POST.get("delete_bill") == "on":
                        delete_bill_permission = Permission.objects.get(codename="delete_bill")
                        employee.user_permissions.add(delete_bill_permission)

                    if request.POST.get("add_documents") is not None and request.POST.get("add_documents") == "on":
                        add_documents_permission = Permission.objects.get(codename="add_documents")
                        add_folder_permission = Permission.objects.get(codename="add_folder")
                        change_folder_permission = Permission.objects.get(codename="chenge_folder")
                        employee.user_permissions.add(add_documents_permission)
                        employee.user_permissions.add(add_folder_permission)
                        employee.user_permissions.add(change_folder_permission)

                    if request.POST.get("view_folder") is not None and request.POST.get("view_folder") == "on":
                        view_folder_permission = Permission.objects.get(codename="view_folder")
                        employee.user_permissions.add(view_folder_permission)

                    if request.POST.get("delete_folder") is not None and request.POST.get("delete_folder") == "on":
                        delete_folder_permission = Permission.objects.get(codename="delete_folder")
                        employee.user_permissions.add(delete_folder_permission)

                    employee.save()

                    messages.success(request, "Funcionário Cadastrado! Solicite que o funcionário cadastre uma senha clicando"
                                              "no email recebido por ele.")

                    return redirect(reverse('info:dashboard'))

            except IntegrityError:

                messages.error(request, "O email do funcionário já está em uso por outro usuário! Utilize outro email")

    form = AddEmployeeForm(request.POST or None)
    try:
        features = ResidentFeatures.objects.get(condominium=condominium)
    except ResidentFeatures.DoesNotExist:
        features = ResidentFeatures()
        features.condominium = condominium
        features.save()
    context = {'form': form,
               'user': condominium,
               'features': features
               }
    return render(request, "info/condominium/employee/add_employee.html", context=context)


@login_required(login_url='info:sign-in')
def edit_employee(request, id):

    condominium = CondominiumProfile.objects.get(pk=int(request.user.id))
    employee = condominium.get_employees().get(pk=id)

    if request.method == "POST":

        # apartment = Con.objects.get(pk=int(request.POST.get('apartment')))
        form = AddEmployeeForm(request.POST)
        if form.is_valid():

            employee.user_permissions.clear()

            if request.POST.get("view_apartment") is not None and request.POST.get("view_apartment") == "on":
                view_appartment_permission = Permission.objects.get(codename="view_apartment")
                employee.user_permissions.add(view_appartment_permission)
            else:
                view_appartment_permission = Permission.objects.get(codename="view_apartment")
                employee.user_permissions.remove(view_appartment_permission)

            if request.POST.get("add_apartment") is not None and request.POST.get("add_apartment") == "on":
                add_appartment_permission = Permission.objects.get(codename="add_apartment")
                employee.user_permissions.add(add_appartment_permission)
            else:
                add_appartment_permission = Permission.objects.get(codename="add_apartment")
                employee.user_permissions.remove(add_appartment_permission)

            if request.POST.get("view_resident") is not None and request.POST.get("view_resident") == "on":
                view_resident_permission = Permission.objects.get(codename="view_resident")
                employee.user_permissions.add(view_resident_permission)
            else:
                view_resident_permission = Permission.objects.get(codename="view_resident")
                employee.user_permissions.remove(view_resident_permission)

            if request.POST.get("add_resident") is not None and request.POST.get("add_resident") == "on":
                add_resident_permission = Permission.objects.get(codename="add_resident")
                employee.user_permissions.add(add_resident_permission)
            else:
                add_resident_permission = Permission.objects.get(codename="add_resident")
                employee.user_permissions.remove(add_resident_permission)

            if request.POST.get("change_resident") is not None and request.POST.get("change_resident") == "on":
                change_resident_permission = Permission.objects.get(codename="change_resident")
                employee.user_permissions.add(change_resident_permission)
            else:
                change_resident_permission = Permission.objects.get(codename="change_resident")
                employee.user_permissions.remove(change_resident_permission)

            if request.POST.get("contact_resident") is not None and request.POST.get("contact_resident") == "on":
                contact_resident_permission = Permission.objects.get(codename="contact_resident")
                employee.user_permissions.add(contact_resident_permission)
            else:
                contact_resident_permission = Permission.objects.get(codename="contact_resident")
                employee.user_permissions.remove(contact_resident_permission)

            if request.POST.get("change_visitant") is not None and request.POST.get("change_visitant") == "on":
                change_visitant_permission = Permission.objects.get(codename="change_visitant")
                employee.user_permissions.add(change_visitant_permission)
            else:
                change_visitant_permission = Permission.objects.get(codename="change_visitant")
                employee.user_permissions.remove(change_visitant_permission)

            if request.POST.get("view_informative") is not None and request.POST.get("view_informative") == "on":
                view_informative_permission = Permission.objects.get(codename="view_informative")
                employee.user_permissions.add(view_informative_permission)
            else:
                view_informative_permission = Permission.objects.get(codename="view_informative")
                employee.user_permissions.remove(view_informative_permission)

            if request.POST.get("add_informative") is not None and request.POST.get("add_informative") == "on":
                add_informative_permission = Permission.objects.get(codename="add_informative")
                employee.user_permissions.add(add_informative_permission)
            else:
                add_informative_permission = Permission.objects.get(codename="add_informative")
                employee.user_permissions.remove(add_informative_permission)

            if request.POST.get("change_informative") is not None and request.POST.get("change_informative") == "on":
                change_informative_permission = Permission.objects.get(codename="change_informative")
                employee.user_permissions.add(change_informative_permission)
            else:
                change_informative_permission = Permission.objects.get(codename="change_informative")
                employee.user_permissions.remove(change_informative_permission)

            if request.POST.get("delete_informative") is not None and request.POST.get("delete_informative") == "on":
                delete_informative_permission = Permission.objects.get(codename="delete_informative")
                employee.user_permissions.add(delete_informative_permission)
            else:
                delete_informative_permission = Permission.objects.get(codename="delete_informative")
                employee.user_permissions.remove(delete_informative_permission)

            if request.POST.get("export_informative") is not None and request.POST.get("export_informative") == "on":
                export_informative_permission = Permission.objects.get(codename="export_informative")
                employee.user_permissions.add(export_informative_permission)
            else:
                export_informative_permission = Permission.objects.get(codename="export_informative")
                employee.user_permissions.remove(export_informative_permission)

            if request.POST.get("view_order") is not None and request.POST.get("view_order") == "on":
                view_order_permission = Permission.objects.get(codename="view_order")
                employee.user_permissions.add(view_order_permission)
            else:
                view_order_permission = Permission.objects.get(codename="view_order")
                employee.user_permissions.remove(view_order_permission)

            if request.POST.get("add_order") is not None and request.POST.get("add_order") == "on":
                add_order_permission = Permission.objects.get(codename="add_order")
                employee.user_permissions.add(add_order_permission)
            else:
                add_order_permission = Permission.objects.get(codename="add_order")
                employee.user_permissions.remove(add_order_permission)

            if request.POST.get("change_order") is not None and request.POST.get("change_order") == "on":
                change_order_permission = Permission.objects.get(codename="change_order")
                employee.user_permissions.add(change_order_permission)
            else:
                change_order_permission = Permission.objects.get(codename="change_order")
                employee.user_permissions.remove(change_order_permission)

            if request.POST.get("view_message") is not None and request.POST.get("view_message") == "on":
                view_message_permission = Permission.objects.get(codename="view_message")
                employee.user_permissions.add(view_message_permission)
            else:
                view_message_permission = Permission.objects.get(codename="view_message")
                employee.user_permissions.add(view_message_permission)

            if request.POST.get("add_message") is not None and request.POST.get("add_message") == "on":
                add_message_permission = Permission.objects.get(codename="add_message")
                employee.user_permissions.add(add_message_permission)
            else:
                add_message_permission = Permission.objects.get(codename="add_message")
                employee.user_permissions.remove(add_message_permission)

            if request.POST.get("add_message_block") is not None and request.POST.get("add_message_block") == "on":
                add_message_block_permission = Permission.objects.get(codename="add_message_block")
                employee.user_permissions.add(add_message_block_permission)
            else:
                add_message_block_permission = Permission.objects.get(codename="add_message_block")
                employee.user_permissions.remove(add_message_block_permission)

            if request.POST.get("add_message_all") is not None and request.POST.get("add_message_all") == "on":
                add_message_all_permission = Permission.objects.get(codename="add_message_all")
                employee.user_permissions.add(add_message_all_permission)
            else:
                add_message_all_permission = Permission.objects.get(codename="add_message_all")
                employee.user_permissions.remove(add_message_all_permission)

            if request.POST.get("view_review") is not None and request.POST.get("view_review") == "on":
                view_review_permission = Permission.objects.get(codename="view_review")
                employee.user_permissions.add(view_review_permission)
            else:
                view_review_permission = Permission.objects.get(codename="view_review")
                employee.user_permissions.remove(view_review_permission)

            if request.POST.get("add_review") is not None and request.POST.get("add_review") == "on":
                add_review_permission = Permission.objects.get(codename="add_review")
                employee.user_permissions.add(add_review_permission)
            else:
                add_review_permission = Permission.objects.get(codename="add_review")
                employee.user_permissions.remove(add_review_permission)

            if request.POST.get("view_surveymodel") is not None and request.POST.get("view_surveymodel") == "on":
                view_surveymodel_permission = Permission.objects.get(codename="view_surveymodel")
                employee.user_permissions.add(view_surveymodel_permission)
            else:
                view_surveymodel_permission = Permission.objects.get(codename="view_surveymodel")
                employee.user_permissions.remove(view_surveymodel_permission)

            if request.POST.get("add_surveymodel") is not None and request.POST.get("add_surveymodel") == "on":
                add_surveymodel_permission = Permission.objects.get(codename="add_surveymodel")
                employee.user_permissions.add(add_surveymodel_permission)
            else:
                add_surveymodel_permission = Permission.objects.get(codename="add_surveymodel")
                employee.user_permissions.remove(add_surveymodel_permission)

            if request.POST.get("add_contract") is not None and request.POST.get("add_contract") == "on":
                add_contract_permission = Permission.objects.get(codename="add_contract")
                employee.user_permissions.add(add_contract_permission)
            else:
                add_contract_permission = Permission.objects.get(codename="add_contract")
                employee.user_permissions.remove(add_contract_permission)

            if request.POST.get("view_contract") is not None and request.POST.get("view_contract") == "on":
                view_contract_permission = Permission.objects.get(codename="view_contract")
                employee.user_permissions.add(view_contract_permission)
            else:
                view_contract_permission = Permission.objects.get(codename="view_contract")
                employee.user_permissions.remove(view_contract_permission)

            if request.POST.get("delete_contract") is not None and request.POST.get("delete_contract") == "on":
                delete_contract_permission = Permission.objects.get(codename="delete_contract")
                employee.user_permissions.add(delete_contract_permission)
            else:
                delete_contract_permission = Permission.objects.get(codename="delete_contract")
                employee.user_permissions.remove(delete_contract_permission)

            if request.POST.get("change_contract") is not None and request.POST.get("change_contract") == "on":
                change_contract_permission = Permission.objects.get(codename="change_contract")
                employee.user_permissions.add(change_contract_permission)
            else:
                change_contract_permission = Permission.objects.get(codename="change_contract")
                employee.user_permissions.remove(change_contract_permission)

            if request.POST.get("view_checklist") is not None and request.POST.get("view_checklist") == "on":
                view_checklist_permission = Permission.objects.get(codename="view_checklist")
                change_task_permission = Permission.objects.get(codename="change_task")
                employee.user_permissions.add(view_checklist_permission)
                employee.user_permissions.add(change_task_permission)
            else:
                view_checklist_permission = Permission.objects.get(codename="view_checklist")
                change_task_permission = Permission.objects.get(codename="change_task")
                employee.user_permissions.remove(view_checklist_permission)
                employee.user_permissions.remove(change_task_permission)

            if request.POST.get("add_checklist") is not None and request.POST.get("add_checklist") == "on":
                add_checklist_permission = Permission.objects.get(codename="add_checklist")
                employee.user_permissions.add(add_checklist_permission)
            else:
                add_checklist_permission = Permission.objects.get(codename="add_checklist")
                employee.user_permissions.remove(add_checklist_permission)

            if request.POST.get("view_userlocation") is not None and request.POST.get("view_userlocation") == "on":
                view_userlocation_permission = Permission.objects.get(codename="view_userlocation")
                employee.user_permissions.add(view_userlocation_permission)
            else:
                view_userlocation_permission = Permission.objects.get(codename="view_userlocation")
                employee.user_permissions.remove(view_userlocation_permission)

            if request.POST.get("activity_report") is not None and request.POST.get("activity_report") == "on":
                activity_report_permission = Permission.objects.get(codename="activity_report")
                employee.user_permissions.add(activity_report_permission)
            else:
                activity_report_permission = Permission.objects.get(codename="activity_report")
                employee.user_permissions.remove(activity_report_permission)

            if request.POST.get("order_report") is not None and request.POST.get("order_report") == "on":
                order_report_permission = Permission.objects.get(codename="order_report")
                employee.user_permissions.add(order_report_permission)
            else:
                order_report_permission = Permission.objects.get(codename="order_report")
                employee.user_permissions.remove(order_report_permission)

            if request.POST.get("message_report") is not None and request.POST.get("message_report") == "on":
                message_report_permission = Permission.objects.get(codename="message_report")
                employee.user_permissions.add(message_report_permission)
            else:
                message_report_permission = Permission.objects.get(codename="message_report")
                employee.user_permissions.remove(message_report_permission)

            if request.POST.get("checklist_report") is not None and request.POST.get("checklist_report") == "on":
                checklist_report_permission = Permission.objects.get(codename="checklist_report")
                employee.user_permissions.add(checklist_report_permission)
            else:
                checklist_report_permission = Permission.objects.get(codename="checklist_report")
                employee.user_permissions.remove(checklist_report_permission)

            if request.POST.get("contract_report") is not None and request.POST.get("contract_report") == "on":
                contract_report_permission = Permission.objects.get(codename="contract_report")
                employee.user_permissions.add(contract_report_permission)
            else:
                contract_report_permission = Permission.objects.get(codename="contract_report")
                employee.user_permissions.remove(contract_report_permission)

            if request.POST.get("survey_report") is not None and request.POST.get("survey_report") == "on":
                survey_report_permission = Permission.objects.get(codename="survey_report")
                employee.user_permissions.add(survey_report_permission)
            else:
                survey_report_permission = Permission.objects.get(codename="survey_report")
                employee.user_permissions.remove(survey_report_permission)

            if request.POST.get("review_report") is not None and request.POST.get("review_report") == "on":
                review_report_permission = Permission.objects.get(codename="review_report")
                employee.user_permissions.add(review_report_permission)
            else:
                review_report_permission = Permission.objects.get(codename="review_report")
                employee.user_permissions.remove(review_report_permission)

            if request.POST.get("resident_report") is not None and request.POST.get("resident_report") == "on":
                resident_report_permission = Permission.objects.get(codename="resident_report")
                employee.user_permissions.add(resident_report_permission)
            else:
                resident_report_permission = Permission.objects.get(codename="resident_report")
                employee.user_permissions.remove(resident_report_permission)

            if request.POST.get("location_report") is not None and request.POST.get("location_report") == "on":
                location_report_permission = Permission.objects.get(codename="location_report")
                employee.user_permissions.add(location_report_permission)
            else:
                location_report_permission = Permission.objects.get(codename="location_report")
                employee.user_permissions.remove(location_report_permission)

            if request.POST.get("visitant_report") is not None and request.POST.get("visitant_report") == "on":
                visitant_report_permission = Permission.objects.get(codename="visitant_report")
                employee.user_permissions.add(visitant_report_permission)
            else:
                visitant_report_permission = Permission.objects.get(codename="visitant_report")
                employee.user_permissions.remove(visitant_report_permission)

            if request.POST.get("add_product") is not None and request.POST.get("add_product") == "on":
                add_product_permission = Permission.objects.get(codename="add_product")
                employee.user_permissions.add(add_product_permission)
            else:
                add_product_permission = Permission.objects.get(codename="add_product")
                employee.user_permissions.remove(add_product_permission)

            if request.POST.get("add_storageentry") is not None and request.POST.get("add_storageentry") == "on":
                add_storageentry_permission = Permission.objects.get(codename="add_storageentry")
                employee.user_permissions.add(add_storageentry_permission)
            else:
                add_storageentry_permission = Permission.objects.get(codename="add_storageentry")
                employee.user_permissions.remove(add_storageentry_permission)

            if request.POST.get("storage_report") is not None and request.POST.get("storage_report") == "on":
                storage_report_permission = Permission.objects.get(codename="storage_report")
                employee.user_permissions.add(storage_report_permission)
            else:
                storage_report_permission = Permission.objects.get(codename="storage_report")
                employee.user_permissions.remove(storage_report_permission)

            if request.POST.get("add_timeline") is not None and request.POST.get("add_timeline") == "on":
                add_timeline_permission = Permission.objects.get(codename="add_timeline")
                employee.user_permissions.add(add_timeline_permission)
            else:
                add_timeline_permission = Permission.objects.get(codename="add_timeline")
                employee.user_permissions.remove(add_timeline_permission)

            if request.POST.get("view_timeline") is not None and request.POST.get("view_timeline") == "on":
                view_timeline_permission = Permission.objects.get(codename="view_timeline")
                employee.user_permissions.add(view_timeline_permission)
            else:
                view_timeline_permission = Permission.objects.get(codename="view_timeline")
                employee.user_permissions.remove(view_timeline_permission)

            if request.POST.get("timeline_report") is not None and request.POST.get("timeline_report") == "on":
                timeline_report_permission = Permission.objects.get(codename="timeline_report")
                employee.user_permissions.add(timeline_report_permission)
            else:
                timeline_report_permission = Permission.objects.get(codename="timeline_report")
                employee.user_permissions.remove(timeline_report_permission)

            if request.POST.get("add_bill") is not None and request.POST.get("add_bill") == "on":
                add_bill_permission = Permission.objects.get(codename="add_bill")
                change_bill_permission = Permission.objects.get(codename="change_bill")
                employee.user_permissions.add(add_bill_permission)
                employee.user_permissions.add(change_bill_permission)
            else:
                add_bill_permission = Permission.objects.get(codename="add_bill")
                change_bill_permission = Permission.objects.get(codename="change_bill")
                employee.user_permissions.remove(add_bill_permission)
                employee.user_permissions.remove(change_bill_permission)

            if request.POST.get("view_bill") is not None and request.POST.get("view_bill") == "on":
                view_bill_permission = Permission.objects.get(codename="view_bill")
                employee.user_permissions.add(view_bill_permission)
            else:
                view_bill_permission = Permission.objects.get(codename="view_bill")
                employee.user_permissions.remove(view_bill_permission)

            if request.POST.get("delete_bill") is not None and request.POST.get("delete_bill") == "on":
                delete_bill_permission = Permission.objects.get(codename="delete_bill")
                employee.user_permissions.add(delete_bill_permission)
            else:
                delete_bill_permission = Permission.objects.get(codename="delete_bill")
                employee.user_permissions.remove(delete_bill_permission)

            if request.POST.get("add_documents") is not None and request.POST.get("add_documents") == "on":
                add_documents_permission = Permission.objects.get(codename="add_documents")
                add_folder_permission = Permission.objects.get(codename="add_folder")
                change_folder_permission = Permission.objects.get(codename="chenge_folder")
                employee.user_permissions.add(add_documents_permission)
                employee.user_permissions.add(add_folder_permission)
                employee.user_permissions.add(change_folder_permission)
            else:
                add_documents_permission = Permission.objects.get(codename="add_documents")
                add_folder_permission = Permission.objects.get(codename="add_folder")
                change_folder_permission = Permission.objects.get(codename="chenge_folder")
                employee.user_permissions.remove(add_documents_permission)
                employee.user_permissions.remove(add_folder_permission)
                employee.user_permissions.remove(change_folder_permission)

            if request.POST.get("view_folder") is not None and request.POST.get("view_folder") == "on":
                view_folder_permission = Permission.objects.get(codename="view_folder")
                employee.user_permissions.add(view_folder_permission)
            else:
                view_folder_permission = Permission.objects.get(codename="view_folder")
                employee.user_permissions.remove(view_folder_permission)

            if request.POST.get("delete_folder") is not None and request.POST.get("delete_folder") == "on":
                delete_folder_permission = Permission.objects.get(codename="delete_folder")
                employee.user_permissions.add(delete_folder_permission)
            else:
                delete_folder_permission = Permission.objects.get(codename="delete_folder")
                employee.user_permissions.remove(delete_folder_permission)

            employee.save()

            messages.success(request, "Funcionário Atualizado!")

            return redirect(reverse('info:employees'))

    form = AddEmployeeForm(request.POST or None)

    form.fields['employee_name'].initial = employee.condominium_name
    form.fields['employee_name'].widget.attrs['readonly'] = True
    form.fields['email'].initial = employee.email
    form.fields['email'].widget.attrs['readonly'] = True

    context = {'form': form, 'employee': employee,
               'user': condominium,
               }
    return render(request, "info/condominium/employee/edit_employee.html", context=context)


@login_required(login_url='info:sign-in')
def delete_employee(request, id):
    condominium = CondominiumProfile.objects.get(pk=int(request.user.id))

    try:
        employee = condominium.get_employees().get(pk=id)
        if employee:
            employee.delete()
            messages.success(request, "Funcionário removido!")
            return redirect('info:employees')
        else:
            messages.error(request, "Funcionário não encontrado!")
            return redirect('info:dashboard')

    except CondominiumProfile.DoesNotExist:
        messages.error(request, "Funcionário não encontrado!")
        return redirect('info:dashboard')


@login_required(login_url='info:sign-in')
def view_employee(request, id):
    condominium = CondominiumProfile.objects.get(pk=int(request.user.id))

    try:
        employee = condominium.get_employees().get(pk=id)
        if employee:
            form = AddEmployeeForm()
            form.fields['employee_name'].initial = employee.condominium_name
            form.fields['employee_name'].disabled = True
            form.fields['email'].initial = employee.email
            form.fields['email'].disabled = True

            context = {'form': form, 'employee': employee, 'user': condominium }
            return render(request, "info/condominium/employee/view_employee.html", context=context)

        else:
            messages.error(request, "Funcionário não encontrado!")
            return redirect('info:dashboard')

    except CondominiumProfile.DoesNotExist:
        messages.error(request, "Funcionário não encontrado!")
        return redirect('info:dashboard')


# def grant_all_permissions(request):
#     for condomínio in CondominiumProfile.objects.all():
#         _def_user_all_permissions(condomínio)
#
#     messages.success(request, "Permissões concedidas!")
#
#     return redirect(reverse('info:dashboard'))
