import datetime
from datetime import date, timedelta

import pytz
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse

from info.forms import ContractForm, ViewContractForm, EditContractForm
from info.models import CondominiumProfile, Contract, HowTo
from info.utils import get_condominium


FIXED_TZ = pytz.timezone("America/Sao_Paulo")

@login_required(login_url='info:sign-in')
def add_contract_expiration(request):
    condominium = get_condominium(request)

    form = ContractForm(request.POST or None, files=request.FILES or None)

    if request.method == "POST":
        if form.is_valid():
            domain = get_current_site(request)
            if int(form.cleaned_data['days_to_notify']) == 31:
                create_contract(condominium, form.cleaned_data, 1, domain)
                create_contract(condominium, form.cleaned_data, 7, domain)
                create_contract(condominium, form.cleaned_data, 15, domain)
                create_contract(condominium, form.cleaned_data, 30, domain)
            else:
                create_contract(condominium, form.cleaned_data, int(form.cleaned_data['days_to_notify']), domain)

        messages.success(request, "Contrato adicionado, o responsável será notificado no tempo selecionado!")

        return redirect(reverse('info:dashboard'))

    context = {'form': form,
               }
    return render(request, "info/condominium/contract/add_contract.html", context=context)


def create_contract(condominium, data, days_to_notify, domain):
    contract = Contract()
    contract.condominium = condominium
    contract.item = data['item']
    contract.description = data['description'] or ""
    if data['image']:
        contract.image = data['image']
    contract.last_maintenance = data['last_maintenance']
    contract.next_maintenance = data['next_maintenance']
    contract.to_email = data['to_email']
    contract.days_to_notify = days_to_notify
    contract.domain = domain
    contract.notify_day = contract.next_maintenance - timedelta(contract.days_to_notify)
    if contract.notify_day > datetime.datetime.now(FIXED_TZ).date():
        contract.save()


@login_required(login_url='info:sign-in')
def contracts(request):
    condominium = get_condominium(request)
    contracts_list = Contract.objects.filter(condominium=condominium).order_by("notify_day")

    search_item = request.GET.get('item')

    if search_item:
        contracts_list = contracts_list.filter(item__contains=search_item)

    search_last_maintenance = request.GET.get('last_maintenance')

    if search_last_maintenance:
        contracts_list = contracts_list.filter(last_maintenance__exact=search_last_maintenance)

    search_next_maintenance = request.GET.get('next_maintenance')

    if search_next_maintenance:
        contracts_list = contracts_list.filter(next_maintenance__exact=search_next_maintenance)

    search_email = request.GET.get('email')

    if search_email:
        contracts_list = contracts_list.filter(email__contains=search_email)

    search_notify_day = request.GET.get('notify_day')

    if search_notify_day:
        contracts_list = contracts_list.filter(notify_day__exact=search_notify_day)

    context = {'contracts': contracts_list,
               'user': condominium
               }

    how_to_contract_list = HowTo.objects.get(name__exact="Vencimentos > Listagem")
    if how_to_contract_list.kind == "Texto":
        context['how_to_contract_list_text'] = how_to_contract_list.value
    else:
        context['how_to_contract_list_link'] = how_to_contract_list.value
    return render(request, "info/condominium/contract/contracts.html", context=context)


@login_required(login_url='info:sign-in')
def delete_contract(request, id):
    condominium = get_condominium(request)
    contract = get_object_or_404(Contract, pk=id, condominium=condominium)
    if contract:
        contract.delete()
        messages.success(request, "Notificação Cancelada!")
        return redirect('info:contracts')
    else:
        messages.error(request, "Contrato não encontrado!")
        return redirect('info:dashboard')


@login_required(login_url='info:sign-in')
def view_contract(request, id):
    condominium = get_condominium(request)
    contract = get_object_or_404(Contract, pk=id, condominium=condominium)
    contract.last_maintenance = contract.last_maintenance.strftime('%d/%m/%Y')
    contract.next_maintenance = contract.next_maintenance.strftime('%d/%m/%Y')
    contract.notify_day = contract.notify_day.strftime('%d/%m/%Y')
    form = ViewContractForm(instance=contract)

    context = {'form': form,
               'id': contract.id,
               }

    if contract.image:
        context['img'] = contract.image

    return render(request, "info/condominium/contract/view_contract.html", context=context)


@login_required(login_url='info:sign-in')
def edit_contract(request, id):
    condominium = get_condominium(request)
    contract = get_object_or_404(Contract, pk=id, condominium=condominium)

    form = EditContractForm(instance=contract)

    if request.method == "POST":
        form = EditContractForm(request.POST)
        if form.is_valid() and form.has_changed():
            contract.item = form.cleaned_data['item']
            contract.description = form.cleaned_data['description']
            contract.image = form.cleaned_data['image']
            contract.last_maintenance = form.cleaned_data['last_maintenance']
            contract.next_maintenance = form.cleaned_data['next_maintenance']
            contract.to_email = form.cleaned_data['to_email']
            contract.notify_day = form.cleaned_data['notify_day']
            if contract.notify_day > datetime.datetime.now(FIXED_TZ).date():
                contract.save()
                messages.success(request, "Contrato atualizado!")
                return redirect(reverse('info:view-contract', args=[int(contract.id)]))
            else:
                messages.success(request, "Data para notificação inválida. Deve ser maior que a data de hoje!")

    context = {'form': form}

    return render(request, "info/condominium/contract/edit_contract.html", context=context)
