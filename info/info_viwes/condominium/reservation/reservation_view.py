import copy

import hashlib
import time

import pytz
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.db.models import Count, Q
from django.forms import modelformset_factory, formset_factory
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils import timezone
from datetime import datetime, timedelta, time as datetime_time

from urllib3 import request

from info.forms import AddApartmentForm, AddedApartmentForm, AddResidentForm, UpdateResidentForm, AddVisitantForm, \
    RegisterVisitant, AddBlockForm, ViewUserForm, ResidentActivityForm, ViewResidentActivityForm, \
    ResidentActivityAnswerForm, ResidentActivityAddAnswerForm, AddVisitantSecurityForm, AddPlaceForm, \
    AddReservationTime, BlockedDateForm, BookingForm, CondominiumReservationLimitsForm, BlockedDateModelForm, \
    ViewBookingForm, PayBookingForm
from info.info_viwes.condominium.report.report_view import visitant_report, export_reservation
from info.info_viwes.condominium.whatsapp_api.whatsapp_view import send_booking_message
from info.info_viwes.condominium_view import send_bill_to_email
from info.models import CondominiumProfile, Apartment, Block, Resident, HowTo, Visitant, VisitantReport, \
    ResidentActivity, ResidentActivityAnswer, Place, ReservationTime, BlockedDay, Reservation, \
    CondominiumReservationLimits, Bill, MessagesInformation
from info.utils import get_condominium, add_signature_to_data, add_manager_notification, add_notification
from info.views import email


FIXED_TZ = pytz.timezone("America/Sao_Paulo")


@login_required(login_url='info:sign-in')
def booking(request):
    condominium = get_condominium(request)

    reservation_db = Reservation.objects.filter(condominium=condominium, removed_by_manager=False).order_by("-created")

    search_area = request.GET.get('area')
    search_date = request.GET.get('date')
    search_resident = request.GET.get('resident')
    search_block = request.GET.get('block')
    search_apartment = request.GET.get('apartment')
    search_status = request.GET.get('status')

    if search_area:
        reservation_db = reservation_db.filter(place__name__contains=search_area)

    if search_date:
        reservation_db = reservation_db.filter(date__exact=search_date)

    if search_resident:
        reservation_db = reservation_db.filter(resident__condominium_name__contains=search_resident)

    if search_status:
        reservation_db = reservation_db.filter(status=search_status)

    reservation = []
    for _reservation in reservation_db:

        resident = Resident.objects.get(name=_reservation.resident.condominium_name,
                                        email=_reservation.resident.email)

        added = False
        if search_block and resident.apartment.block.name.find(search_block) != -1:
            reservation_obj = {
                'id': _reservation.id,
                'place': _reservation.place,
                'time': _reservation.time,
                'resident': _reservation.resident,
                'status': _reservation.status,
                'date': _reservation.date,
                'created': _reservation.created.astimezone(FIXED_TZ),
                'block': resident.apartment.block.name,
                'apartment': str(resident.apartment.number) + " " + resident.apartment.complement,
                'wait_payment': _reservation.wait_payment,
                'approved_by': _reservation.approved_by,
                'canceled_by': _reservation.canceled_by,
            }
            reservation.append(reservation_obj)
            added = True

        if search_apartment and str(str(resident.apartment.number) + " " + resident.apartment.complement).find(
                search_apartment) != -1 and not added:
            reservation_obj = {
                'id': _reservation.id,
                'place': _reservation.place,
                'time': _reservation.time,
                'resident': _reservation.resident,
                'status': _reservation.status,
                'date': _reservation.date,
                'created': _reservation.created.astimezone(FIXED_TZ),
                'block': resident.apartment.block.name,
                'apartment': str(resident.apartment.number) + " " + resident.apartment.complement,
                'wait_payment': _reservation.wait_payment,
                'approved_by': _reservation.approved_by,
                'canceled_by': _reservation.canceled_by,
            }
            reservation.append(reservation_obj)

        if not search_block and not search_apartment:
            reservation_obj = {
                'id': _reservation.id,
                'place': _reservation.place,
                'time': _reservation.time,
                'resident': _reservation.resident,
                'status': _reservation.status,
                'date': _reservation.date,
                'created': _reservation.created.astimezone(FIXED_TZ),
                'block': resident.apartment.block.name,
                'apartment': str(resident.apartment.number) + " " + resident.apartment.complement,
                'wait_payment': _reservation.wait_payment,
                'approved_by': _reservation.approved_by,
                'canceled_by': _reservation.canceled_by,
            }
            reservation.append(reservation_obj)

    context = {'user': condominium,
               'reservation': reservation
               }
    return render(request, "info/condominium/reservation/reservation.html", context=context)


@login_required(login_url='info:sign-in')
def add_place(request):
    condominium = get_condominium(request)

    form = AddPlaceForm(request.POST or None, files=request.FILES or None, condominium=condominium)

    if request.method == 'POST':

        if form.is_valid():
            place = Place()
            place.condominium = condominium
            place.name = form.cleaned_data['name']
            place.description = form.cleaned_data['description']
            place.capacity = form.cleaned_data['capacity']
            place.price = form.cleaned_data['price']
            place.rules = form.cleaned_data['rules']
            place.inspection = form.cleaned_data['inspection']
            place.minimum_days_to_cancel = form.cleaned_data['minimum_days_to_cancel']
            place.internal_regime = form.cleaned_data['internal_regime']
            place.acceptance_terms = form.cleaned_data['acceptance_terms']
            place.maximum_unity_reservation_per_day = form.cleaned_data['maximum_unity_reservation_per_day']
            place.maximum_resident_reservation_per_day = form.cleaned_data['maximum_resident_reservation_per_day']
            place.maximum_unity_reservation_per_week = form.cleaned_data['maximum_unity_reservation_per_week']
            place.maximum_resident_reservation_per_week = form.cleaned_data['maximum_resident_reservation_per_week']
            place.maximum_unity_reservation_per_month = form.cleaned_data['maximum_unity_reservation_per_month']
            place.maximum_resident_reservation_per_month = form.cleaned_data['maximum_resident_reservation_per_month']
            place.maximum_unity_reservation_per_year = form.cleaned_data['maximum_unity_reservation_per_year']
            place.maximum_resident_reservation_per_year = form.cleaned_data['maximum_resident_reservation_per_year']
            place.minimum_days_to_reserve = form.cleaned_data['minimum_days_to_reserve']
            place.maximum_days_to_booking = form.cleaned_data['maximum_days_to_booking']
            place.auto_confirmation = request.POST.get('auto_confirmation') is not None and request.POST.get(
                'auto_confirmation') == "on"

            place.image = form.cleaned_data['image']
            place.multi_reservations = request.POST.get('multi_reservations') is not None and request.POST.get(
                'multi_reservations') == "on"
            if request.POST.get('allow_new'):
                if int(request.POST.get('allow_new')) > 0:
                    place.allow_new_reservation = int(request.POST.get('allow_new'))

            place.save()
            place.blocked_areas.set(form.cleaned_data['blocked_areas'])
            place.save()

            messages.success(request, "Local Cadastrado!")
            return redirect(reverse('info:add-time', args=[int(place.id)]))
        else:
            messages.error(request, form.errors)

    context = {'form': form, }

    return render(request, "info/condominium/reservation/add_place.html", context=context)


@login_required(login_url='info:sign-in')
def places(request):
    condominium = get_condominium(request)
    places = Place.objects.filter(condominium=condominium)
    context = {'places': places, }
    return render(request, "info/condominium/reservation/places.html", context=context)


@login_required(login_url='info:sign-in')
def resident_places(request):
    condominium = get_condominium(request)
    places = Place.objects.filter(condominium=condominium, hidden=False)
    context = {'places': places, }
    return render(request, "info/condominium/reservation/resident_places.html", context=context)


@login_required(login_url='info:sign-in')
def add_time(request, id):
    condominium = get_condominium(request)

    BlockedDaysFormset = formset_factory(form=BlockedDateForm, extra=0)
    blocked_formset = BlockedDaysFormset(request.POST or None, prefix="blocked")

    if request.method == 'POST':

        form = AddReservationTime(request.POST)

        if form.is_valid():

            initial = form.cleaned_data['init_time']
            until = form.cleaned_data['end_time']

            if until <= initial:
                until = datetime_time(23, 59)

            interval = form.cleaned_data['interval']

            init_time = initial
            current_datetime = datetime.now(FIXED_TZ)

            while until > init_time >= initial:

                init_datetime = datetime.combine(current_datetime.date(), init_time)
                if interval == "30" or interval == "45" or interval == "90":
                    end_time = init_datetime + timedelta(minutes=int(interval))
                elif interval == "24":
                    end_time = datetime.combine(current_datetime.date(), until)
                else:
                    end_time = init_datetime + timedelta(hours=int(interval))

                if end_time.time() > until:
                    end_time = until

                time = ReservationTime()
                time.condominium = condominium
                time.init_time = init_datetime.time()
                time.end_time = end_time.time()

                time.blocked = request.POST.get('blocked') is not None and request.POST.get('blocked') == "on"

                selected_days = "monday,tuesday,wednesday,thursday,friday,saturday,sunday,"
                selected_days = _check_selected_days(request, selected_days, "monday")
                selected_days = _check_selected_days(request, selected_days, "tuesday")
                selected_days = _check_selected_days(request, selected_days, "wednesday")
                selected_days = _check_selected_days(request, selected_days, "thursday")
                selected_days = _check_selected_days(request, selected_days, "friday")
                selected_days = _check_selected_days(request, selected_days, "saturday")
                selected_days = _check_selected_days(request, selected_days, "sunday")

                # time.day = ",".join(form.cleaned_data['selected_days'])
                time.day = selected_days
                time.place = Place.objects.get(pk=int(id))
                time.save()
                _save_blocked_day(blocked_formset, condominium, time.place)

                init_time = end_time.time()

            messages.success(request, "Horários Cadastrados!")
            return redirect('info:dashboard')
        else:
            messages.error(request, form.errors)

    form = AddReservationTime()

    context = {'form': form,
               'blocked_formset': blocked_formset}

    return render(request, "info/condominium/reservation/add_time.html", context=context)


@login_required(login_url='info:sign-in')
def edit_time(request, id):
    condominium = get_condominium(request)
    place = Place.objects.get(pk=int(id))

    BlockedDaysFormset = modelformset_factory(BlockedDay, form=BlockedDateModelForm, extra=0)
    queryset = BlockedDay.objects.filter(condominium=condominium, place=place)
    blocked_formset = BlockedDaysFormset(request.POST or None, queryset=queryset, prefix="blocked")

    if request.method == 'POST':

        form = AddReservationTime(request.POST)

        if form.is_valid():
            user = CondominiumProfile.objects.get(pk=int(request.user.id))
            for reservation in Reservation.objects.filter(condominium=condominium, place=place):
                reservation.status = "CANCELADA"
                reservation.canceled_by = user.condominium_name
                reservation.save()

            for time in ReservationTime.objects.filter(condominium=condominium, place=place):
                time.delete()

            initial = form.cleaned_data['init_time']
            until = form.cleaned_data['end_time']
            interval = form.cleaned_data['interval']

            init_time = initial
            current_datetime = datetime.now(FIXED_TZ)

            while until > init_time >= initial:

                init_datetime = datetime.combine(current_datetime.date(), init_time)
                if interval == "30" or interval == "45" or interval == "90":
                    end_time = init_datetime + timedelta(minutes=int(interval))
                else:
                    end_time = init_datetime + timedelta(hours=int(interval))

                if end_time.time() > until:
                    end_time = until

                time = ReservationTime()
                time.condominium = condominium
                time.init_time = init_datetime.time()
                time.end_time = end_time.time()

                time.blocked = request.POST.get('blocked') is not None and request.POST.get('blocked') == "on"

                selected_days = "monday,tuesday,wednesday,thursday,friday,saturday,sunday,"
                selected_days = _check_selected_days(request, selected_days, "monday")
                selected_days = _check_selected_days(request, selected_days, "tuesday")
                selected_days = _check_selected_days(request, selected_days, "wednesday")
                selected_days = _check_selected_days(request, selected_days, "thursday")
                selected_days = _check_selected_days(request, selected_days, "friday")
                selected_days = _check_selected_days(request, selected_days, "saturday")
                selected_days = _check_selected_days(request, selected_days, "sunday")

                # time.day = ",".join(form.cleaned_data['selected_days'])
                time.day = selected_days
                time.place = Place.objects.get(pk=int(id))
                time.save()

                _save_blocked_day(blocked_formset, condominium, time.place)

                init_time = end_time.time()

            messages.success(request, "Horários Cadastrados!")
            return redirect('info:dashboard')
        else:
            messages.error(request, form.errors)

    times = ReservationTime.objects.filter(condominium=condominium, place=place)

    time = times.first()

    start_datetime = datetime.combine(datetime.today(), time.init_time)
    end_datetime = datetime.combine(datetime.today(), time.end_time)

    time_difference = end_datetime - start_datetime
    minutes_difference = time_difference.total_seconds() / 60

    time.end_time = times.last().end_time

    form = AddReservationTime(instance=time)

    if minutes_difference == 30 or minutes_difference == 45 or minutes_difference == 90:
        form.fields['interval'].initial = str(minutes_difference)
    else:
        form.fields['interval'].initial = str(minutes_difference / 60)

    checked = []
    if "monday" not in time.day:
        checked.append("monday")

    if "tuesday" not in time.day:
        checked.append("tuesday")

    if "wednesday" not in time.day:
        checked.append("wednesday")

    if "thursday" not in time.day:
        checked.append("thursday")

    if "friday" not in time.day:
        checked.append("friday")

    if "saturday" not in time.day:
        checked.append("saturday")

    if "sunday" not in time.day:
        checked.append("sunday")

    context = {'form': form,
               'blocked_formset': blocked_formset,
               'checked': checked}

    return render(request, "info/condominium/reservation/edit_time.html", context=context)


@login_required(login_url='info:sign-in')
def delete_place(request, id):
    condominium = get_condominium(request)
    place = get_object_or_404(Place, pk=id, condominium=condominium)
    if place:
        place.delete()
        messages.success(request, "Local Removido!")
        return redirect('info:places')
    else:
        messages.error(request, "Local não encontrado!")
        return redirect('info:dashboard')


@login_required(login_url='info:sign-in')
def edit_place(request, id):
    condominium = get_condominium(request)
    place = get_object_or_404(Place, pk=id, condominium=condominium)

    if request.method == 'POST':
        form = AddPlaceForm(request.POST, files=request.FILES or None, condominium=condominium)
        if form.is_valid():
            place.name = form.cleaned_data['name']
            place.description = form.cleaned_data['description']
            place.capacity = form.cleaned_data['capacity']
            place.price = form.cleaned_data['price']
            place.rules = form.cleaned_data['rules']
            place.inspection = form.cleaned_data['inspection']
            place.minimum_days_to_cancel = form.cleaned_data['minimum_days_to_cancel']
            place.internal_regime = form.cleaned_data['internal_regime']
            place.acceptance_terms = form.cleaned_data['acceptance_terms']
            place.maximum_unity_reservation_per_day = form.cleaned_data['maximum_unity_reservation_per_day']
            place.maximum_resident_reservation_per_day = form.cleaned_data['maximum_resident_reservation_per_day']
            place.maximum_unity_reservation_per_week = form.cleaned_data['maximum_unity_reservation_per_week']
            place.maximum_resident_reservation_per_week = form.cleaned_data['maximum_resident_reservation_per_week']
            place.maximum_unity_reservation_per_month = form.cleaned_data['maximum_unity_reservation_per_month']
            place.maximum_resident_reservation_per_month = form.cleaned_data['maximum_resident_reservation_per_month']
            place.maximum_unity_reservation_per_year = form.cleaned_data['maximum_unity_reservation_per_year']
            place.maximum_resident_reservation_per_year = form.cleaned_data['maximum_resident_reservation_per_year']
            place.minimum_days_to_reserve = form.cleaned_data['minimum_days_to_reserve']
            place.maximum_days_to_booking = form.cleaned_data['maximum_days_to_booking']
            place.auto_confirmation = request.POST.get('auto_confirmation') is not None and request.POST.get(
                'auto_confirmation') == "on"

            if form.cleaned_data['image']:
                place.image = form.cleaned_data['image']

            place.multi_reservations = request.POST.get('multi_reservations') is not None and request.POST.get(
                'multi_reservations') == "on"
            if request.POST.get('allow_new'):
                if int(request.POST.get('allow_new')) > 0:
                    place.allow_new_reservation = int(request.POST.get('allow_new'))

            place.save()
            place.blocked_areas.set(form.cleaned_data['blocked_areas'])
            place.save()

            messages.success(request, "Local Atualizado!")
            return redirect('info:dashboard')
        else:
            messages.error(request, form.errors)

    form = AddPlaceForm(instance=place, condominium=condominium)
    context = {'form': form, 'place': place}

    return render(request, "info/condominium/reservation/edit_place.html", context=context)


@login_required(login_url='info:sign-in')
def booking_detail(request, id):
    condominium = get_condominium(request)
    place = get_object_or_404(Place, pk=id, condominium=condominium)
    context = {'place': place}

    return render(request, "info/condominium/reservation/place_detail.html", context=context)


@login_required(login_url='info:sign-in')
def booking_manager_detail(request, id):
    condominium = get_condominium(request)
    place = get_object_or_404(Place, pk=id, condominium=condominium)
    context = {'place': place}

    return render(request, "info/condominium/reservation/manage_place.html", context=context)


def hide_place(request, id):
    condominium = get_condominium(request)
    place = get_object_or_404(Place, pk=id, condominium=condominium)
    hidden = request.GET.get('hide')
    place.hidden = hidden
    place.save()

    return JsonResponse({}, safe=False)


def notify_booking(request, id):
    condominium = get_condominium(request)
    place = get_object_or_404(Place, pk=id, condominium=condominium)
    notify = request.GET.get('notify')
    place.notification = notify
    place.save()

    return JsonResponse({}, safe=False)


@login_required(login_url='info:sign-in')
def booking_date(request, id):
    condominium = get_condominium(request)
    place = get_object_or_404(Place, pk=id, condominium=condominium)
    user = CondominiumProfile.objects.get(pk=int(request.user.id))

    if user.defaulter:
        messages.error(request, "Acesso bloqueado!")
        messages.error(request, "Favor entrar em contato com sua administradora para maiores informações")
        return redirect(reverse('info:booking-detail', args=[int(id)]))

    users = _get_users_from_unity(user)

    try:
        limit = CondominiumReservationLimits.objects.get(condominium=condominium)
        success, message = _check_condomínium_limits(user, limit)
        if not success:
            messages.error(request, message)
            return redirect(reverse('info:booking-detail', args=[int(id)]))
    except CondominiumReservationLimits.DoesNotExist:
        pass

    if _today_resident_reservation_by_place(user, place) >= place.maximum_resident_reservation_per_day:
        messages.error(request, "Você atingiu o limite de reservas desta área por hoje!")
        return redirect(reverse('info:booking-detail', args=[int(id)]))

    sum = 0
    for _user in users:
        sum += _today_resident_reservation_by_place(_user, place)

    if sum >= place.maximum_unity_reservation_per_day:
        messages.error(request, "Seu apartamento atingiu o limite de reservas desta área por hoje!")
        return redirect(reverse('info:booking-detail', args=[int(id)]))

    if _week_resident_reservation_by_place(user, place) >= place.maximum_resident_reservation_per_week:
        messages.error(request, "Você atingiu o limite de reservas desta área para esta semana!")
        return redirect(reverse('info:booking-detail', args=[int(id)]))

    sum = 0
    for _user in users:
        sum += _week_resident_reservation_by_place(_user, place)

    if sum >= place.maximum_unity_reservation_per_week:
        messages.error(request, "Seu apartamento atingiu o limite de reservas desta área para esta semana!")
        return redirect(reverse('info:booking-detail', args=[int(id)]))

    if _month_resident_reservation_by_place(user, place) >= place.maximum_resident_reservation_per_month:
        messages.error(request, "Você atingiu o limite de reservas desta área para este mês!")
        return redirect(reverse('info:booking-detail', args=[int(id)]))

    sum = 0
    for _user in users:
        sum += _month_resident_reservation_by_place(_user, place)

    if sum >= place.maximum_unity_reservation_per_month:
        messages.error(request, "Seu apartamento atingiu o limite de reservas desta área para este mês!")
        return redirect(reverse('info:booking-detail', args=[int(id)]))

    if _year_resident_reservation_by_place(user, place) >= place.maximum_resident_reservation_per_year:
        messages.error(request, "Você atingiu o limite de reservas desta área para este ano!")
        return redirect(reverse('info:booking-detail', args=[int(id)]))

    sum = 0
    for _user in users:
        sum += _year_resident_reservation_by_place(_user, place)

    if sum >= place.maximum_unity_reservation_per_year:
        messages.error(request, "Seu apartamento atingiu o limite de reservas desta área para este ano!")
        return redirect(reverse('info:booking-detail', args=[int(id)]))

    for _user in users:
        unused_reservations = Reservation.objects.filter(condominium=condominium, resident=_user, place=place,
                                                         date__gte=datetime.now(FIXED_TZ)).order_by("date")

        if unused_reservations.count() and unused_reservations.count() >= place.allow_new_reservation:
            messages.error(request,
                           "Você atingiu o limite de reserva não usadas para esta área! Só poderá fazer uma nova reserva após o dia " + unused_reservations.first().date.date().strftime(
                               '%d/%m/%Y'))
            return redirect(reverse('info:booking-detail', args=[int(id)]))

    form = BookingForm()

    if request.method == 'POST':
        date = request.POST.get('date')

        selected_datetime = datetime.strptime(date, '%Y-%m-%d')
        if selected_datetime.date() < datetime.now(FIXED_TZ).date():
            messages.error(request, "Esta data já passou e não pode ser escolhida!")
            return redirect(reverse('info:booking-date', args=[int(place.id)]))

        days = selected_datetime.date() - datetime.now(FIXED_TZ).date()
        if days.days > place.maximum_days_to_booking:
            messages.error(request, "Máximo de dias de antescedência atingido, selecione uma data nos próximos "
                           + str(place.maximum_days_to_booking) + " dias!")
            return redirect(reverse('info:booking-date', args=[int(place.id)]))

        if days.days < place.minimum_days_to_reserve:
            messages.error(request, "Mínimo de dias de antescedência atingido, selecione uma data a partir dos próximos "
                           + str(place.minimum_days_to_reserve) + " dias!")
            return redirect(reverse('info:booking-date', args=[int(place.id)]))

        try:
            blocked = BlockedDay.objects.get(condominium=condominium, place=place, blocked_day__exact=date)
            day_of_week = _get_week_day(date)
            times = ReservationTime.objects.filter(
                Q(place=place),
                Q(condominum=condominium),
                Q(blocked=False),
                Q(day__contains=day_of_week),
                Q(init_time__lt=blocked.init_time) | Q(init_time__gt=blocked.end_time)
            )

            if not len(times):
                messages.error(request, "Nenhuma horário disponível nesta data!")
                return redirect(reverse('info:booking-date', args=[int(place.id)]))

        except BlockedDay.DoesNotExist:
            day_of_week = _get_week_day(date)
            times = ReservationTime.objects.filter(condominium=condominium, place=place, day__contains=day_of_week,
                                                   blocked=False).order_by('init_time')
            if not place.multi_reservations:

                bookings = Reservation.objects.filter(place=place, date=date)
                for booking in bookings:
                    times = times.exclude(init_time__exact=booking.time.init_time)

            if not len(times):
                messages.error(request, "Nenhuma horário disponível nesta data!")
                return redirect(reverse('info:booking-date', args=[int(place.id)]))

        context = {'place': place, 'times': times, 'date': date}
        return render(request, 'info/condominium/reservation/booking_times.html', context=context)

    bookings = Reservation.objects.filter(condominium=condominium, place=place,
                                          date__gte=datetime.now(FIXED_TZ))

    search_date = request.GET.get('search_date')

    if search_date:
        bookings = bookings.filter(date__exact=search_date)

    search_time = request.GET.get('search_time')

    if search_time:
        bookings = bookings.filter(time__init_time__lte=search_time, time__end_time__gte=search_time)

    search_resident = request.GET.get('search_resident')

    if search_resident:
        bookings = bookings.filter(resident__condominium_name__contains=search_resident)

    confirmed_days = []
    pending_days = []
    unavailable_days = []

    current_date = datetime.now(FIXED_TZ).date()

    for i in range(place.maximum_days_to_booking):

        current_date += timedelta(days=1)
        confirmed = Reservation.objects.filter(place=place, condominium=condominium, date__exact=current_date,
                                               status__exact="CONFIRMADA")
        if confirmed:
            confirmed_days.append(current_date.strftime("%Y-%m-%d"))

        pending = Reservation.objects.filter(place=place, condominium=condominium, date__exact=current_date,
                                             status__exact="PENDENTE")
        if pending:
            pending_days.append(current_date.strftime("%Y-%m-%d"))

        week_day = _get_week_day(current_date.strftime("%Y-%m-%d"))
        m_time = ReservationTime.objects.filter(place=place).first()
        if m_time:
            if m_time.day.find(week_day) == -1:
                unavailable_days.append(current_date.strftime("%Y-%m-%d"))

    context = {'form': form, 'place': place, 'reservation': bookings,  'confirmed_days': confirmed_days,
               'pending_days': pending_days, 'unavailable_days': unavailable_days}

    return render(request, "info/condominium/reservation/booking_date.html", context=context)


@login_required(login_url='info:sign-in')
def reservation(request, place_id, time_id, date):
    condominium = get_condominium(request)
    user = CondominiumProfile.objects.get(pk=int(request.user.id))
    place = get_object_or_404(Place, pk=int(place_id), condominium=condominium)
    time = get_object_or_404(ReservationTime, pk=int(time_id), condominium=condominium)

    # if not place.multi_reservations:
    #     time.blocked = True
    #     time.save()

    booking = Reservation()
    booking.condominium = condominium
    booking.place = place
    booking.time = time
    booking.resident = user
    if place.auto_confirmation:
        booking.status = "CONFIRMADA"
        booking.approved_by = "Reserva Automática"
        add_notification(condominium, [user.email],
                         "Sua reserva da " + place.name.upper() +
                         " foi confirmada!. Verifique sua caixa de entrada, lixo eletrônico ou no menu aplicação",
                         request, "/my-booking")
        if place.notification:
            add_manager_notification(condominium,
                                     "NOVA RESERVA DA ÁREA " + booking.place.name.upper() +
                                     " CONFIRMADA AUTOMATICAMENTE.", request)
    else:
        booking.status = "PENDENTE"
    booking.date = date
    booking.save()

    if place.price and place.notification:
        add_manager_notification(condominium,
                                 "NOVA SOLICITAÇÃO DE RESERVA DA ÁREA " + booking.place.name.upper() +
                                 ". FAÇA A COBRANÇA AO MORADOR.", request)

    messages.success(request, "Reserva solicitada com sucesso!")
    return redirect('info:booking-places')


def confirm_reservation(request, place_id, time_id, date):
    condominium = get_condominium(request)
    user = CondominiumProfile.objects.get(pk=int(request.user.id))

    if user.defaulter:
        messages.error(request, "Acesso bloqueado!")
        messages.error(request, "Favor entrar em contato com sua administradora para maiores informações")
        return redirect(reverse('info:dashboard'))

    place = get_object_or_404(Place, pk=int(place_id), condominium=condominium)
    time = get_object_or_404(ReservationTime, pk=int(time_id), condominium=condominium)

    context = {
        'place': place,
        'time': time,
        'date': datetime.strptime(date, "%Y-%m-%d")
    }

    return render(request, "info/condominium/reservation/confirm_booking.html", context=context)


@login_required(login_url='info:sign-in')
@permission_required('info.my_booking', login_url='info:sign-in')
def my_reservation(request):
    condominium = get_condominium(request)
    user = CondominiumProfile.objects.get(pk=int(request.user.id))

    try:
        users = _get_users_from_unity(user)
        reservation = (Reservation.objects.filter(condominium=condominium, resident=user,
                                                  removed_by_user=False).order_by("-created") |
                       Reservation.objects.filter(condominium=condominium, resident__in=users, removed_by_user=False))
    except Resident.DoesNotExist:
        reservation = Reservation.objects.filter(condominium=condominium, resident=user,
                                                 removed_by_user=False).order_by("-created")

    context = {
        'reservation': reservation
    }
    return render(request, "info/condominium/reservation/my_reservation.html", context=context)


@login_required(login_url='info:sign-in')
def export_to_pdf(request, id):
    condominium = get_condominium(request)

    booking = Reservation.objects.get(pk=int(id))

    return export_reservation(request, condominium, [booking])



@login_required(login_url='info:sign-in')
def cancel_reservation(request, id):
    reservation = Reservation.objects.get(pk=int(id))
    user = CondominiumProfile.objects.get(pk=int(request.user.id))
    current_datetime = datetime.now(FIXED_TZ)
    end_time = current_datetime + timedelta(days=int(reservation.place.minimum_days_to_cancel))

    if reservation.date.date() >= end_time.date():
        reservation.status = "CANCELADA"
        reservation.canceled_by = user.condominium_name
        reservation.save()

        time = get_object_or_404(ReservationTime, pk=reservation.time.pk)
        time.blocked = False
        time.save()

        condominium = get_condominium(request)

        if condominium.whatsapp_notification:
            try:
                messages_info = MessagesInformation.objects.get(condominium=condominium)
            except MessagesInformation.DoesNotExist:
                messages_info = MessagesInformation()
                messages_info.condominium = condominium
                messages_info.save()

            if messages_info.allow_charge or messages_info.messages_used <= messages_info.messages_limit:

                send_booking_message(condominium.condominium_name,
                                     reservation.place.name,
                                     reservation.resident.condominium_name,
                                     reservation.resident.whatsapp,
                                     "reserva_cancelada")

                messages_info.messages_used = messages_info.messages_used + 1
                messages_info.save()

        messages.success(request, "Reserva cancelada!")
    else:
        messages.error(request,
                       "Você já não pode cancelar esta reserva pois ultrapassa os dias mínimos para cancelamento!")

    if user.resident_in:
        return redirect('info:my-booking')
    return redirect('info:booking')


@login_required(login_url='info:sign-in')
def validate_paymewnt(request, id):
    reservation = Reservation.objects.get(pk=int(id))

    context = {'reservation': reservation}

    return render(request, "info/condominium/reservation/approve_payment.html", context=context)


@login_required(login_url='info:sign-in')
def approve_reservation(request, id):
    user = CondominiumProfile.objects.get(pk=int(request.user.id))
    condominium = get_condominium(request)
    reservation = Reservation.objects.get(pk=int(id))
    reservation.status = "CONFIRMADA"
    reservation.wait_payment = False
    reservation.approved_by = user.condominium_name
    reservation.save()
    add_notification(condominium, [reservation.resident.email],
                     "Sua reserva da " + reservation.place.name.upper() +
                     " foi confirmada!. Verifique sua caixa de entrada, lixo eletrônico ou no menu aplicação", request)

    if condominium.whatsapp_notification:
        try:
            messages_info = MessagesInformation.objects.get(condominium=condominium)
        except MessagesInformation.DoesNotExist:
            messages_info = MessagesInformation()
            messages_info.condominium = condominium
            messages_info.save()

        if messages_info.allow_charge or messages_info.messages_used <= messages_info.messages_limit:
            send_booking_message(condominium.condominium_name,
                                              reservation.place.name,
                                              reservation.resident.condominium_name,
                                              reservation.resident.whatsapp,
                                              "reserva_confirmada")

            messages_info.messages_used = messages_info.messages_used + 1
            messages_info.save()

    if reservation.place.notification:
        add_manager_notification(condominium,
                                 "NOVA RESERVA DA ÁREA " + booking.place.name.upper() +
                                 " CONFIRMADA.", request, "/my-booking")
    messages.success(request, "Reserva aprovada!")

    return redirect('info:booking')


@login_required(login_url='info:sign-in')
def add_bill(request, id):
    condominium = get_condominium(request)
    reservation = Reservation.objects.get(pk=int(id))

    form = ViewBookingForm(instance=reservation)

    if request.method == 'POST':

        form = AddReservationTime(request.POST, request.FILES)

        reservation.link = request.POST.get('link') or ""
        reservation.bill = request.FILES.get('bill') or None
        reservation.save()

        if reservation.link or reservation.bill:
            reservation.wait_payment = True
            reservation.save()

            bill = Bill()
            bill.user = reservation.resident
            bill.condominium = condominium
            bill.file = reservation.bill
            bill.sender = condominium.condominium_name
            bill.save()

            send_bill_to_email(request, reservation.resident, reservation.bill)

            add_notification(condominium, [reservation.resident.email],
                             "Uma cobraça para a reserva da " + reservation.place.name.upper() +
                             " foi solicitada a você. Verifique sua caixa de entrada, lixo eletrônico ou no menu aplicação",
                             request, "/my-booking")
            messages.success(request,
                             "Cobrança enviada com sucesso! Aguarde a pagamento por parte do morador.")
            return redirect(reverse('info:booking'))

    context = {'form': form, 'reservation': reservation}

    return render(request, "info/condominium/reservation/add_bill.html", context=context)


@login_required(login_url='info:sign-in')
def add_payment(request, id):
    condominium = get_condominium(request)
    reservation = Reservation.objects.get(pk=int(id))

    form = PayBookingForm(instance=reservation)

    if request.method == 'POST':

        form = AddReservationTime(request.POST, request.FILES)

        reservation.payment = request.FILES.get('payment') or None
        reservation.save()

        if reservation.payment:
            add_manager_notification(condominium,
                                     "NOVO PAGAMENTO RECEBIDO PARA A RESERVA DA ÁREA " + reservation.place.name.upper() +
                                     ". Faça a validação do comprovante nos detalhes das reservas.", request)
            messages.success(request,
                             "Comprovante enviado com sucesso! Aguarde a aprovação por parte do administrador.")
            return redirect(reverse('info:my-booking'))

    context = {'form': form, 'reservation': reservation}

    return render(request, "info/condominium/reservation/add_payment.html", context=context)


@login_required(login_url='info:sign-in')
def delete_reservation(request, id):
    user = CondominiumProfile.objects.get(pk=int(request.user.id))
    booking = get_object_or_404(Reservation, pk=id)
    if user.resident_in:
        booking.removed_by_user = True
    else:
        booking.removed_by_manager = True
    booking.save()

    messages.success(request, "Reserva excluída!")

    if user.resident_in:
        return redirect('info:my-booking')
    return redirect('info:booking')


@login_required(login_url='info:sign-in')
def add_condominium_limits(request):
    condominium = get_condominium(request)

    try:
        instance = CondominiumReservationLimits.objects.get(condominium=condominium)
        form = CondominiumReservationLimitsForm(instance=instance)
    except CondominiumReservationLimits.DoesNotExist:
        form = CondominiumReservationLimitsForm()

    if request.method == 'POST':

        form = CondominiumReservationLimitsForm(request.POST)

        if form.is_valid():
            try:
                limit = CondominiumReservationLimits.objects.get(condominium=condominium)
                limit.maximum_unity_reservation_per_day = form.cleaned_data['maximum_unity_reservation_per_day']
                limit.maximum_resident_reservation_per_day = form.cleaned_data['maximum_resident_reservation_per_day']
                limit.maximum_unity_reservation_per_week = form.cleaned_data['maximum_unity_reservation_per_week']
                limit.maximum_resident_reservation_per_week = form.cleaned_data['maximum_resident_reservation_per_week']
                limit.maximum_unity_reservation_per_month = form.cleaned_data['maximum_unity_reservation_per_month']
                limit.maximum_resident_reservation_per_month = form.cleaned_data[
                    'maximum_resident_reservation_per_month']
                limit.maximum_unity_reservation_per_year = form.cleaned_data['maximum_unity_reservation_per_year']
                limit.maximum_resident_reservation_per_year = form.cleaned_data['maximum_resident_reservation_per_year']
                limit.save()
            except CondominiumReservationLimits.DoesNotExist:

                limit = form.save(commit=False)
                limit.condominium = condominium
                limit.save()

            messages.success(request, "Limites Cadastrados!")
            return redirect(reverse('info:booking'))
        else:
            messages.error(request, form.errors)

    context = {'form': form, }

    return render(request, "info/condominium/reservation/add_limit.html", context=context)


def _today_resident_reservation_by_place(resident, place):
    today = datetime.now(FIXED_TZ).date()
    return Reservation.objects.filter(
        resident=resident,
        place=place,
        created=today
    ).count()


def _today_resident_reservation(resident):
    today = datetime.now(FIXED_TZ).date()
    return Reservation.objects.filter(
        resident=resident,
        created=today
    ).count()


def _week_resident_reservation_by_place(resident, place):
    today = datetime.now(FIXED_TZ).date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    return Reservation.objects.filter(
        Q(resident=resident),
        Q(place=place),
        Q(created__gte=start_of_week) & Q(created__lte=end_of_week)
    ).count()


def _week_resident_reservation(resident):
    today = datetime.now(FIXED_TZ).date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    return Reservation.objects.filter(
        Q(resident=resident),
        Q(created__gte=start_of_week) & Q(created__lte=end_of_week)
    ).count()


def _month_resident_reservation_by_place(resident, place):
    today = datetime.now(FIXED_TZ).date()
    start_of_month = today.replace(day=1)
    end_of_month = start_of_month.replace(month=start_of_month.month + 1) - timedelta(days=1)

    return Reservation.objects.filter(
        Q(resident=resident),
        Q(place=place),
        Q(created__gte=start_of_month) & Q(created__lte=end_of_month)
    ).count()


def _month_resident_reservation(resident):
    today = datetime.now(FIXED_TZ).date()
    start_of_month = today.replace(day=1)
    end_of_month = start_of_month.replace(month=start_of_month.month + 1) - timedelta(days=1)

    return Reservation.objects.filter(
        Q(resident=resident),
        Q(created__gte=start_of_month) & Q(created__lte=end_of_month)
    ).count()


def _year_resident_reservation_by_place(resident, place):
    today = datetime.now(FIXED_TZ).date()
    start_of_year = today.replace(month=1, day=1)
    end_of_year = start_of_year.replace(year=start_of_year.year + 1) - timedelta(days=1)

    return Reservation.objects.filter(
        Q(resident=resident),
        Q(place=place),
        Q(created__gte=start_of_year) & Q(created__lte=end_of_year)
    ).count()


def _year_resident_reservation(resident):
    today = datetime.now(FIXED_TZ).date()
    start_of_year = today.replace(month=1, day=1)
    end_of_year = start_of_year.replace(year=start_of_year.year + 1) - timedelta(days=1)

    return Reservation.objects.filter(
        Q(resident=resident),
        Q(created__gte=start_of_year) & Q(created__lte=end_of_year)
    ).count()


def _check_condomínium_limits(user, limit):
    if _today_resident_reservation(user) >= limit.maximum_resident_reservation_per_day:
        return False, "Você atingiu o limite geral de reservas por hoje!"

    users = _get_users_from_unity(user)

    sum = 0
    for _user in users:
        sum += _today_resident_reservation(_user)

    if sum >= limit.maximum_unity_reservation_per_day:
        return False, "Seu atingiu o limite geral de reservas por hoje!"

    if _week_resident_reservation(user) >= limit.maximum_resident_reservation_per_week:
        return False, "Você atingiu o limite geral de reservas para esta semana!"

    sum = 0
    for _user in users:
        sum += _week_resident_reservation(_user)

    if sum >= limit.maximum_unity_reservation_per_week:
        return False, "Seu atingiu o limite geral de reservas para esta semana!"

    if _month_resident_reservation(user) >= limit.maximum_resident_reservation_per_month:
        return False, "Você atingiu o limite geral de reservas para este mês!"

    sum = 0
    for _user in users:
        sum += _month_resident_reservation(_user)

    if sum >= limit.maximum_unity_reservation_per_month:
        return False, "Seu atingiu o limite geral de reservas para este mês!"

    if _year_resident_reservation(user) >= limit.maximum_resident_reservation_per_year:
        return False, "Você atingiu o limite geral de reservas para este ano!"

    sum = 0
    for _user in users:
        sum += _year_resident_reservation(_user)

    if sum >= limit.maximum_unity_reservation_per_year:
        return False, "Seu atingiu o limite geral de reservas para este ano!"

    return True, ""


def _get_users_from_unity(user):
    try:
        resident = Resident.objects.get(email=user.email, name=user.condominium_name)
        residents = Resident.objects.filter(apartment=resident.apartment)
        users = []

        for _resident in residents:
            try:
                _user = CondominiumProfile.objects.get(condominium_name=_resident.name, email=_resident.email)
                users.append(_user)
            except CondominiumProfile.DoesNotExist:
                continue
        return users
    except Resident.DoesNotExist:
        return []


def _check_selected_days(request, selected, day):
    if request.POST.get(day):
        selected = selected.replace(day + ',', '')
    return selected


def _save_blocked_day(formset, condominium, place):
    if all([formset.is_valid(), ]):
        for blocked_form in formset:
            if blocked_form.has_changed():
                try:
                    BlockedDay.objects.get(condominium=condominium,
                                           blocked_day=blocked_form.cleaned_data['blocked_day'], place=place)
                except BlockedDay.DoesNotExist:
                    day = BlockedDay()
                    day.condominium = condominium
                    day.place = place
                    day.blocked_day = blocked_form.cleaned_data['blocked_day']
                    day.init_time = blocked_form.cleaned_data['init_time']
                    day.end_time = blocked_form.cleaned_data['end_time']
                    day.save()


def _get_week_day(date):
    selected_datetime = datetime.strptime(date, '%Y-%m-%d')

    # Get the day of the week as an integer (0 to 6, where Monday is 0)
    day_of_week = selected_datetime.weekday()

    # match day_of_week:
    #     case 0: return "monday"
    #     case 1: return "tuesday"
    #     case 2: return "wednesday"
    #     case 3: return "thursday"
    #     case 4: return "friday"
    #     case 5: return "saturday"
    #     case 6: return "sunday"

    if day_of_week == 0:
        return "monday"
    elif day_of_week == 1:
        return "tuesday"
    elif day_of_week == 2:
        return "wednesday"
    elif day_of_week == 3:
        return "thursday"
    elif day_of_week == 4:
        return "friday"
    elif day_of_week == 5:
        return "saturday"
    elif day_of_week == 6:
        return "sunday"
