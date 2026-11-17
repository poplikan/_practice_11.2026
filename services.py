from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Schedule, Booking

def book_station(user, schedule_id, ticket_type, portions):
    with transaction.atomic():
        schedule = Schedule.objects.select_for_update().get(id=schedule_id)
        
        booked = Booking.objects.filter(schedule=schedule, status='active').count()
        
        if booked >= schedule.hall.station_count:
            raise ValidationError("Свободных станций нет. Выберите другую дату.")
        
        Booking.objects.create(
            user=user, schedule=schedule, 
            booking_type=ticket_type, portions=portions, 
            status='active'
        )