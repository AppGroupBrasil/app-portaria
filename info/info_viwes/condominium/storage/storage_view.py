import datetime
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.forms import modelformset_factory
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags

from info.forms import ContractForm, ViewContractForm, EditContractForm, AddProductForm, StorageEntryForm, \
    StorageWithdrawForm
from info.models import CondominiumProfile, Contract, HowTo, Product, StorageEntry
from info.utils import get_condominium, add_signature_to_data


@login_required(login_url='info:sign-in')
# @permission_required('info.add_storage')
def add_storage_entry(request):
    condominium = get_condominium(request)
    products = Product.objects.filter(condominium=condominium).order_by('name')

    EntrySet = modelformset_factory(StorageEntry, form=StorageEntryForm, extra=1)
    entries_queryset = StorageEntry.objects.none()
    entries_formset = EntrySet(request.POST or None, queryset=entries_queryset,
                               prefix="entry")
    for form in entries_formset:
        form.fields['product'].queryset = products

    context = {
        'title': "Adicionar ao Estoque",
        'entries_formset': entries_formset,
    }

    if entries_formset.is_valid():

        for entry_form in entries_formset:
            if 'product' in entry_form.cleaned_data.keys() and entry_form.cleaned_data['product']:
                if entry_form.cleaned_data['quantity'] >= 0:
                    storage_entry = StorageEntry()
                    storage_entry.condominium = condominium
                    storage_entry.product = entry_form.cleaned_data['product']
                    storage_entry.quantity = entry_form.cleaned_data['quantity']
                    storage_entry.price = entry_form.cleaned_data['price']
                    storage_entry.type = "ENTRADA"
                    storage_entry.worker = CondominiumProfile.objects.get(pk=int(request.user.id))
                    storage_entry.save()
                    product = Product.objects.get(pk=storage_entry.product.id)
                    product.quantity = product.quantity + storage_entry.quantity
                    product.save()
                else:
                    messages.error(request, "Quantidade incálida para o ", entry_form.cleaned_data['product'])

        messages.success(request, "Adicionado ao Estoque!")
        return redirect('info:dashboard')

    else:
        print("entries_formset")
        print(entries_formset.errors)

    return render(request, "info/condominium/storage/add_storage_entry.html", context=context)


@login_required(login_url='info:sign-in')
# @permission_required('info.add_storage')
def withdraw_storage_entry(request):
    condominium = get_condominium(request)
    products = Product.objects.filter(condominium=condominium).order_by('name')

    EntrySet = modelformset_factory(StorageEntry, form=StorageWithdrawForm, extra=1)
    entries_queryset = StorageEntry.objects.none()
    entries_formset = EntrySet(request.POST or None, queryset=entries_queryset,
                               prefix="entry")
    for form in entries_formset:
        form.fields['product'].queryset = products

    context = {
        'title': "Remover do Estoque",
        'entries_formset': entries_formset,
    }

    if entries_formset.is_valid():

        for entry_form in entries_formset:

            if 'product' in entry_form.cleaned_data.keys() and entry_form.cleaned_data['product']:
                product = Product.objects.get(pk=entry_form.cleaned_data['product'].id)

                if entry_form.cleaned_data['quantity'] >= 0 and product.quantity >= entry_form.cleaned_data['quantity']:
                    storage_entry = StorageEntry()
                    storage_entry.condominium = condominium
                    storage_entry.product = entry_form.cleaned_data['product']
                    storage_entry.quantity = entry_form.cleaned_data['quantity']
                    storage_entry.price = 0.0
                    storage_entry.type = "SAÍDA"
                    storage_entry.worker = CondominiumProfile.objects.get(pk=int(request.user.id))
                    storage_entry.save()
                    product = Product.objects.get(pk=storage_entry.product.id)
                    product.quantity = product.quantity - storage_entry.quantity
                    product.save()
                    if product.quantity < product.warning_quantity:
                        _send_storage_warning_email(request, product.name, product.quantity, product.warning_quantity)

                    messages.success(request, "Removido do Estoque!")
                    return redirect('info:dashboard')
                else:
                    messages.error(request, "Quantidade inválida do produto no estoque!")
            else:
                messages.error(request, "Selecione um Produto")
    else:
        print("entries_formset")
        print(entries_formset.errors)

    return render(request, "info/condominium/storage/add_storage_entry.html", context=context)


@login_required(login_url='info:sign-in')
def storage_management(request):
    condominium = get_condominium(request)
    context = {'user': condominium}
    return render(request, "info/condominium/storage/storage_management.html", context=context)


def _send_storage_warning_email(request, name, quantity, minimum):
    subject = 'Quantidade de Produto no estoque abaixo do esperado'
    # data = add_signature_to_data(request)
    data = add_signature_to_data(request)
    data['name'] = name
    data['quantity'] = str(quantity)
    data['minimum'] = str(minimum)
    body = render_to_string(
        'info/condominium/storage/warning.html',
        data
    )
    text_content = strip_tags(body)
    msg = EmailMultiAlternatives(subject, text_content, to=[get_condominium(request).email])
    msg.attach_alternative(body, "text/html")
    msg.send()
