import datetime
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse

from info.forms import ContractForm, ViewContractForm, EditContractForm, AddProductForm, ViewProductForm
from info.models import CondominiumProfile, Contract, HowTo, Product
from info.utils import get_condominium


@login_required(login_url='info:sign-in')
def add_product(request):
    condominium = get_condominium(request)
    form = AddProductForm(request.POST or None, files=request.FILES or None)

    if request.method == "POST":
        if form.is_valid():

            product = Product()
            product.condominium = condominium
            product.name = form.cleaned_data['name']
            product.description = form.cleaned_data['description'] or ""
            if form.cleaned_data['image']:
                product.image = form.cleaned_data['image']
            product.save()

        messages.success(request, "Produto adicionado!")

        return redirect(reverse('info:dashboard'))

    context = {'form': form,
               }
    return render(request, "info/condominium/products/add_product.html", context=context)


@login_required(login_url='info:sign-in')
def products(request):
    condominium = get_condominium(request)
    product_list = Product.objects.filter(condominium=condominium).order_by("name")

    context = {'products': product_list,
               'user': condominium
               }

    # how_to_contract_list = HowTo.objects.get(name__exact="Vencimentos > Listagem")
    # if how_to_contract_list.kind == "Texto":
    #     context['how_to_contract_list_text'] = how_to_contract_list.value
    # else:
    #     context['how_to_contract_list_link'] = how_to_contract_list.value
    return render(request, "info/condominium/products/products.html", context=context)


@login_required(login_url='info:sign-in')
def delete_product(request, id):
    condominium = get_condominium(request)
    product = get_object_or_404(Product, pk=id, condominium=condominium)
    if product:
        product.delete()
        messages.success(request, "Produto Removido!")
        return redirect('info:products')
    else:
        messages.error(request, "Produto não encontrado!")
        return redirect('info:products')


@login_required(login_url='info:sign-in')
def view_product(request, id):
    condominium = get_condominium(request)
    product = get_object_or_404(Product, pk=id, condominium=condominium)

    form = ViewProductForm(instance=product)

    context = {'form': form,
               'id': product.id,
               }

    if product.image:
        context['img'] = product.image

    return render(request, "info/condominium/products/view_product.html", context=context)
#
#
@login_required(login_url='info:sign-in')
def edit_product(request, id):
    condominium = get_condominium(request)
    product = get_object_or_404(Product, pk=id, condominium=condominium)

    form = AddProductForm(instance=product)

    if request.method == "POST":
        form = AddProductForm(request.POST, files=request.FILES or None)
        if form.is_valid() and form.has_changed():
            product.name = form.cleaned_data['name']
            product.description = form.cleaned_data['description'] or ""
            if form.cleaned_data['image']:
                product.image = form.cleaned_data['image']
            product.save()
            messages.success(request, "Produto Atualizado!")
            return redirect('info:products')

    context = {'form': form}

    return render(request, "info/condominium/products/edit_product.html", context=context)
