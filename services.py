from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal
import logging
from datetime import timedelta


from .models import Schedule, Booking, PurchaseList, PurchaseItem, Recipe

logger = logging.getLogger(__name__)


BOOKING_OPEN_HOURS = 24

def booking_is_open(schedule, now=None):
    now = now or timezone.now()
    return (
        schedule.status == "planned"
        and schedule.start_datetime - now > timedelta(hours=BOOKING_OPEN_HOURS)
    )

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
            .select_related('hall', 'masterclass')
            .get(id=schedule_id)
        )

        if not booking_is_open(schedule):
            raise ValidationError("Запись на это занятие закрыта (бронь закрывается за 24 часа до старта).")

        if schedule.start_datetime <= timezone.now():
            raise ValidationError("Нельзя забронировать прошедшее занятие.")

        booked = Booking.objects.filter(
            schedule=schedule,
            status__in=['active', 'paid'],
        ).count()

        if booked >= schedule.hall.station_count:
            logger.warning(
                "Нет свободных станций: schedule=%s, booked=%s, capacity=%s",
                schedule_id, booked, schedule.hall.station_count,
            )
            raise ValidationError("Свободных станций нет. Выберите другую дату.")

        mc = schedule.masterclass
        adult = mc.adult_price
        child = adult * (100 - mc.child_discount) / 100

        if ticket_type == "pair":
            total = (adult + child) * portions
        else:
            total = adult * portions

        booking = Booking.objects.create(
            user=user,
            schedule=schedule,
            ticket_type=ticket_type,
            portions=portions,
            total=total,
            status='active',
        )

        logger.info(
            "Бронь успешно создана: id=%s, user=%s, schedule=%s, total=%s",
            booking.id, user.username, schedule_id, booking.total,
        )
        return booking


def generate_purchase_list(schedule_id):
    """FR-07 + FR-08: собирает закупочный лист по рецептурам и числу порций."""
    with transaction.atomic():
        schedule = Schedule.objects.select_for_update().select_related("masterclass").get(id=schedule_id)

        active = schedule.bookings.filter(status__in=['active', 'paid'])
        total_portions = active.aggregate(s=Sum('portions'))['s'] or 0

        pl, _ = PurchaseList.objects.get_or_create(schedule=schedule)
        pl.total_portions = total_portions
        pl.save(update_fields=['total_portions', 'generated_at'])

        pl.items.all().delete()

        recipes = (
            Recipe.objects
            .filter(dish__masterclasses=schedule.masterclass)
            .select_related("ingredient")
        )
        per_ingredient = {}
        for r in recipes:
            per_ingredient[r.ingredient_id] = (
                per_ingredient.get(r.ingredient_id, Decimal("0"))
                + r.amount_per_portion
            )

        for ing_id, amount in per_ingredient.items():
            PurchaseItem.objects.create(
                purchase_list=pl,
                ingredient_id=ing_id,
                total_amount=(amount * total_portions),
            )

        logger.info(
            "Закупочный лист сформирован: schedule=%s, порций=%s, позиций=%s",
            schedule_id, total_portions, len(per_ingredient),
        )
        return pl