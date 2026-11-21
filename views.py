from datetime import timedelta
from decimal import Decimal
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Count, Sum, Avg, Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string

from .models import (
    MasterClass, Schedule, Booking, Hall, Chef, Cuisine, PurchaseList,
)

def home(request):
    sessions = (
        Schedule.objects
        .filter(start_datetime__gte=timezone.now())
        .select_related("masterclass", "masterclass__cuisine", "hall", "chef")
        .order_by("start_datetime")[:6]
    )
    return render(request, "home.html", {"sessions": sessions})

def catalog(request):
    qs = MasterClass.objects.select_related("cuisine").all()

    # --- поиск по нескольким словам (AND) ---
    q = request.GET.get("q", "").strip()
    if q:
        for word in q.split():
            qs = qs.filter(
                Q(title__icontains=word)
                | Q(description__icontains=word)
                | Q(cuisine__name__icontains=word)
            )

    # --- кухня (FK) ---
    cuisine = request.GET.get("cuisine")
    if cuisine:
        qs = qs.filter(cuisine__name=cuisine)

    # --- шеф (только через Schedule, related_name="schedules") ---
    chef = request.GET.get("chef")
    if chef:
        qs = qs.filter(schedules__chef_id=chef).distinct()

    # --- дата (занятия в этот день) ---
    date = request.GET.get("date")
    if date:
        qs = qs.filter(schedules__start_datetime__date=date).distinct()

    # --- сортировка ---
    sort = request.GET.get("sort")
    if sort == "price":
        qs = qs.order_by("adult_price", "title")
    elif sort == "date":
        qs = qs.order_by("schedules__start_datetime", "title").distinct()
    else:
        qs = qs.order_by("title")   # дефолт — по названию

    context = {
        "workshops": qs,
        "cuisines": Cuisine.objects.values_list("name", "name"),
        "chefs": Chef.objects.all(),
        "total": qs.count(),
    }

    # --- AJAX: отдаём только фрагмент карточек ---
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_to_string(
            "partials/_workshop_cards.html",
            {"workshops": qs},
            request=request,
        )
        return JsonResponse({"html": html, "count": qs.count()})

    return render(request, "catalog.html", context)

def workshop_detail(request, pk):
    item = get_object_or_404(MasterClass, pk=pk)
    sessions = (
        Schedule.objects
        .filter(masterclass=item, start_datetime__gte=timezone.now())
        .select_related("hall", "chef")
        .order_by("start_datetime")
    )
    return render(request, "detail.html", {"item": item, "sessions": sessions})


# ---------- Бронирование ----------

@login_required
def booking_create(request, session_id):
    schedule = get_object_or_404(
        Schedule.objects.select_related("masterclass", "chef", "hall"),
        pk=session_id,
    )
    mc = schedule.masterclass

    if request.method == "POST":
        ticket_type = request.POST.get("ticket_type", "single")
        
        # Считаем порции
        if ticket_type == "pair":
            portions = 2
        else:
            try:
                portions = max(1, min(10, int(request.POST.get("portions", 1))))
            except (TypeError, ValueError):
                portions = 1

        # Считаем цену
        adult = mc.adult_price
        child = adult * (100 - mc.child_discount) / 100
        total = adult + child if ticket_type == "pair" else adult * portions

        # Проверка свободных мест
        occupied = Booking.objects.filter(schedule=schedule).exclude(status="cancelled").count()
        if occupied >= schedule.hall.station_count:
            messages.error(request, "Свободных станций нет")
            return redirect("booking", session_id=schedule.id)

        # Создаем бронь со всеми полями
        Booking.objects.create(
            schedule=schedule,
            user=request.user,
            ticket_type=ticket_type,
            portions=portions,
            total=total,
            status="pending",
        )
        
        messages.success(request, f"Бронь оформлена: {total} ₽")
        return redirect("cabinet")

    return render(request, "booking.html", {"session": schedule})

@login_required
@require_POST
def booking_edit(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    new_type = request.POST.get("ticket_type")
    
    if new_type not in ("single", "pair"):
        messages.error(request, "Некорректный тип билета")
        return redirect("cabinet")

    mc = booking.schedule.masterclass
    adult = mc.adult_price
    child = adult * (100 - mc.child_discount) / 100

    booking.ticket_type = new_type
    if new_type == "pair":
        booking.portions = 2
        booking.total = adult + child
    else:
        booking.portions = 1
        booking.total = adult
    booking.save()
    
    messages.success(request, "Бронь обновлена")
    return redirect("cabinet")

@login_required
@require_POST
def booking_cancel(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    if booking.status != "cancelled":
        booking.status = "cancelled"
        booking.save(update_fields=["status"])
        messages.success(request, "Бронь отменена")
    return redirect("cabinet")


@login_required
def cabinet(request):
    bookings = (
        Booking.objects
        .filter(user=request.user)
        .select_related(
            "schedule", 
            "schedule__masterclass", 
            "schedule__hall"
        )
        .order_by("-id")
    )
    return render(request, "cabinet.html", {"bookings": bookings})


def api_session_seats(request, session_id):
    schedule = get_object_or_404(Schedule, pk=session_id)
    
    # ИСПРАВЛЕНИЕ: используем прямой запрос к Booking, чтобы не зависеть от related_name
    occupied = Booking.objects.filter(schedule=schedule).exclude(status="cancelled").count()
    
    free = max(0, schedule.hall.station_count - occupied)

    booking_open = (
        schedule.status == "planned"
        and schedule.start_datetime - timezone.now() > timedelta(hours=24)
    )
    return JsonResponse({"free": free, "booking_open": booking_open})


# ---------- Регистрация ----------

def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Аккаунт создан")
            return redirect("cabinet")
    else:
        form = UserCreationForm()
    return render(request, "signup.html", {"form": form})


# ---------- Прочее ----------

def policy(request):
    return render(request, "policy.html")


def contacts(request):
    return render(request, "contacts.html")


def purchaser_list(request):
    sessions = Schedule.objects.select_related("masterclass", "hall", "chef").all()
    return render(request, "purchaser.html", {"sessions": sessions})