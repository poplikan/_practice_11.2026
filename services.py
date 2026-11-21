
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Schedule, Booking


def book_station(user, schedule_id, ticket_type, portions):
    # Проверяем тип билета
    if ticket_type not in ('adult', 'pair'):
        raise ValidationError("Выберите корректный тип билета.")

    # Проверяем количество порций
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

        # Проверяем статус и дату занятия
        if schedule.status != 'planned':
            raise ValidationError("Запись на это занятие закрыта.")

        if schedule.start_datetime <= timezone.now():
            raise ValidationError("Нельзя забронировать прошедшее занятие.")

        # Считаем занятые станции
        booked = Booking.objects.filter(
            schedule=schedule,
            status__in=['active', 'paid']
        ).count()

        if booked >= schedule.hall.station_count:
            raise ValidationError(
                "Свободных станций нет. Выберите другую дату."
            )

        # Создаём бронь
        booking = Booking.objects.create(
            user=user,
            schedule=schedule,
            booking_type=ticket_type,
            portions=portions,
            status='active'
        )

        return booking
