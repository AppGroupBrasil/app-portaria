from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from info.info_viwes.condominium.apartment.apartment_view import AUTO_DEPARTURE_NOTE
from info.info_viwes.condominium.vehicle.vehicle_view import AUTO_VEHICLE_CHECKOUT_NOTE
from info.models import Vehicle, Visitant, VisitantReport


def _append_note(value, note, max_length):
    current_value = (value or "").strip()
    if note in current_value:
        return current_value
    if not current_value:
        return note

    allowed_prefix_length = max_length - len(note) - 1
    return f"{current_value[:allowed_prefix_length].rstrip()} {note}"


def _group_duplicate_active_vehicles(condominium_id=None):
    queryset = Vehicle.objects.filter(
        Q(has_leaved=False) | Q(arrived=True)
    ).exclude(
        vehicle_plate__isnull=True,
    ).exclude(
        vehicle_plate__exact="",
    ).order_by('condominium_id', 'vehicle_plate', '-created', '-id')

    if condominium_id:
        queryset = queryset.filter(condominium_id=condominium_id)

    grouped = defaultdict(list)
    for vehicle in queryset:
        grouped[(vehicle.condominium_id, vehicle.vehicle_plate.upper())].append(vehicle)

    return {key: items for key, items in grouped.items() if len(items) > 1}


def _group_duplicate_active_visitants(condominium_id=None):
    queryset = Visitant.objects.filter(
        leaves_in__isnull=True,
        arrived=True,
    ).exclude(
        vehicle_plate__isnull=True,
    ).exclude(
        vehicle_plate__exact="",
    ).order_by('condominium_id', 'vehicle_plate', '-visit_in', '-created', '-id')

    if condominium_id:
        queryset = queryset.filter(condominium_id=condominium_id)

    grouped = defaultdict(list)
    for visitant in queryset:
        grouped[(visitant.condominium_id, visitant.vehicle_plate.upper())].append(visitant)

    return {key: items for key, items in grouped.items() if len(items) > 1}


def _create_visitant_report(visitant):
    VisitantReport.objects.create(
        condominium=visitant.condominium,
        block=visitant.block,
        apartment=visitant.apartment,
        name=visitant.name,
        document=visitant.document,
        comment=visitant.comment,
        until=visitant.until,
        allowed=visitant.allowed,
        security_name=visitant.security_name,
        visit_in=visitant.visit_in,
        leaves_in=visitant.leaves_in,
        photo=visitant.photo,
        vehicle_model=visitant.vehicle_model,
        vehicle_plate=visitant.vehicle_plate,
        resident=visitant.resident,
    )


class Command(BaseCommand):
    help = "Baixa retroativamente placas duplicadas ainda ativas, mantendo apenas o registro mais recente por placa."

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Aplica as baixas. Sem esta flag, o comando roda apenas em modo simulação.',
        )
        parser.add_argument(
            '--scope',
            choices=['all', 'vehicles', 'visitants'],
            default='all',
            help='Escolhe se o saneamento será feito em veículos, visitantes ou ambos.',
        )
        parser.add_argument(
            '--condominium-id',
            type=int,
            help='Limita o saneamento a um condomínio específico.',
        )

    def handle(self, *args, **options):
        apply_changes = options['apply']
        scope = options['scope']
        condominium_id = options.get('condominium_id')

        self.stdout.write(self.style.WARNING(
            'Modo aplicação ativado.' if apply_changes else 'Modo simulação ativado. Nenhum dado será alterado.'
        ))

        if scope in ('all', 'vehicles'):
            self._handle_vehicles(apply_changes, condominium_id)

        if scope in ('all', 'visitants'):
            self._handle_visitants(apply_changes, condominium_id)

    def _handle_vehicles(self, apply_changes, condominium_id):
        duplicates = _group_duplicate_active_vehicles(condominium_id)
        total_closed = 0

        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Veículos com duplicidade ativa'))

        if not duplicates:
            self.stdout.write('Nenhuma placa de veículo com duplicidade ativa encontrada.')
            return

        now = timezone.now()
        for (_, plate), items in duplicates.items():
            keeper = items[0]
            stale_items = items[1:]
            self.stdout.write(f'Placa {plate}: manter ID {keeper.id} e baixar {len(stale_items)} registro(s).')

            for stale_vehicle in stale_items:
                self.stdout.write(f'  - Vehicle ID {stale_vehicle.id} | condomínio {stale_vehicle.condominium_id} | criado {stale_vehicle.created}')
                if apply_changes:
                    stale_vehicle.obs = _append_note(stale_vehicle.obs, AUTO_VEHICLE_CHECKOUT_NOTE, 200)
                    stale_vehicle.has_leaved = True
                    stale_vehicle.arrived = False
                    stale_vehicle.leaved_in = now
                    stale_vehicle.save(update_fields=['obs', 'has_leaved', 'arrived', 'leaved_in'])
                total_closed += 1

        status = 'baixado(s)' if apply_changes else 'identificado(s)'
        self.stdout.write(self.style.SUCCESS(
            f'Veículos analisados: {len(duplicates)} placa(s) duplicada(s), {total_closed} registro(s) {status}.'
        ))

    def _handle_visitants(self, apply_changes, condominium_id):
        duplicates = _group_duplicate_active_visitants(condominium_id)
        total_closed = 0

        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Visitantes com duplicidade ativa'))

        if not duplicates:
            self.stdout.write('Nenhuma placa de visitante com duplicidade ativa encontrada.')
            return

        now = timezone.now()
        for (_, plate), items in duplicates.items():
            keeper = items[0]
            stale_items = items[1:]
            self.stdout.write(f'Placa {plate}: manter ID {keeper.id} e baixar {len(stale_items)} registro(s).')

            for stale_visitant in stale_items:
                self.stdout.write(
                    f'  - Visitant ID {stale_visitant.id} | condomínio {stale_visitant.condominium_id} | chegada {stale_visitant.visit_in or stale_visitant.created}'
                )
                if apply_changes:
                    stale_visitant.comment = _append_note(stale_visitant.comment, AUTO_DEPARTURE_NOTE, 250)
                    stale_visitant.leaves_in = now
                    stale_visitant.arrived = False
                    if stale_visitant.leave_consent:
                        stale_visitant.can_leave = False
                    stale_visitant.save(update_fields=['comment', 'leaves_in', 'arrived', 'can_leave', 'visit_time'])
                    _create_visitant_report(stale_visitant)
                total_closed += 1

        status = 'baixado(s)' if apply_changes else 'identificado(s)'
        self.stdout.write(self.style.SUCCESS(
            f'Visitantes analisados: {len(duplicates)} placa(s) duplicada(s), {total_closed} registro(s) {status}.'
        ))