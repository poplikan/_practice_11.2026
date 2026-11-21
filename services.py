from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Schedule, Booking

def book_station(user, schedule_id, ticket_type, portions):
    if ticket_type not in ('single', 'pair'):
        raise ValidationError("Выберите корректный тип билета.")

    try:
        portions = int(portions)
    except (TypeError, ValueError):
        raise ValidationError("Укажите корректное количество порций.")

    if portions < 1 or portions > 10:
        raise ValidationError("Количество порций должно быть от 1 до 10.")

    with transaction.atomic():
        schedule = (
            Schedule.objects
            .select_for_update()
            .select_related('hall')
            .get(id=schedule_id)
        )

        if schedule.status != 'planned':
            raise ValidationError("Запись на это занятие закрыта.")

        if schedule.start_datetime <= timezone.now():
            raise ValidationError("Нельзя забронировать прошедшее занятие.")

        booked = Booking.objects.filter(
            schedule=schedule,
            status__in=['active', 'paid']
        ).count()

        if booked >= schedule.hall.station_count:
            raise ValidationError("Свободных станций нет. Выберите другую дату.")

        # ПРАВИЛЬНЫЙ РАСЧЕТ
        mc = schedule.masterclass
        adult = mc.adult_price
        child = adult * (100 - mc.child_discount) / 100
        total = adult + child if ticket_type == "pair" else adult * portions

        booking = Booking.objects.create(
            user=user,
            schedule=schedule,
            ticket_type=ticket_type,
            portions=portions,
            total=total,
            status='active'
        )

        return booking