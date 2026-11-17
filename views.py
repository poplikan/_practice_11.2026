from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import MasterClass, Schedule, Booking, PurchaseList
from .services import book_station

def home(request):
    schedules = Schedule.objects.all().order_by('start_datetime')[:3]
    return render(request, 'home.html', {'sessions': schedules})

def catalog(request):
    masterclasses = MasterClass.objects.all()
    
    q = request.GET.get('q')
    if q: 
        masterclasses = masterclasses.filter(title__icontains=q)
    
    cuisine = request.GET.get('cuisine')
    if cuisine: 
        masterclasses = masterclasses.filter(cuisine__name=cuisine)

    return render(request, 'catalog.html', {'workshops': masterclasses})

def workshop_detail(request, pk):
    item = get_object_or_404(MasterClass, pk=pk)
    schedules = item.schedules.all().order_by('start_datetime')
    return render(request, 'detail.html', {'item': item, 'sessions': schedules})

@login_required
def booking_create(request, session_id):
    session = get_object_or_404(Schedule, id=session_id)
    
    if request.method == 'POST':
        ticket_type = request.POST.get('ticket_type')
        portions = int(request.POST.get('portions', 1))
        
        try:
            book_station(request.user, session.id, ticket_type, portions)
            messages.success(request, "Бронь создана. Проверьте почту.")
            return redirect('cabinet')
        except ValidationError as e:
            messages.error(request, str(e))
            
    return render(request, 'booking.html', {'session': session})

@login_required
def cabinet(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-schedule__start_datetime')
    return render(request, 'cabinet.html', {'bookings': bookings})

def purchaser_list(request):
    schedules = Schedule.objects.filter(purchase_list__isnull=False)
    return render(request, 'purchaser.html', {'sessions': schedules})

def policy(request):
    return render(request, 'policy.html')

def contacts(request):
    return render(request, 'contacts.html')