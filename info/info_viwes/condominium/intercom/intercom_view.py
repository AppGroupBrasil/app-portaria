from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from info.models import Resident
from info.utils import get_condominium


@login_required(login_url='info:sign-in')
def contacts(request):
    condominium = get_condominium(request)
    residents_list = Resident.objects.filter(apartment__block__condominium=condominium).order_by("apartment__block")

    search_apartment = request.GET.get('contact_apartment')
    search_name = request.GET.get('contact_name')

    if search_name:
        residents_list = residents_list.filter(name__contains=search_name)

    if search_apartment:
        residents = []
        for resident in residents_list:
            apartment = resident.apartment.block.name + " / " + str(resident.apartment.number) + " " + resident.apartment.complement
            if apartment.__contains__(search_apartment):
                residents.append(resident)
        residents_list = residents

    for resident in residents_list:
        if resident.whatsapp:
            resident.whatsapp = resident.whatsapp.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    context = {'residents': residents_list,
               }
    return render(request, "info/condominium/intercom/contacts.html", context=context)
