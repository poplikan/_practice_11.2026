from datetime import timedelta
from decimal import Decimal
import csv
from io import StringIO
import logging

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.db.models import Count, Sum, Avg, Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth import logout as auth_logout
from .forms import ChefSignUpForm
from .services import (
    book_station, generate_purchase_list,
    occupied_seats, booking_is_open, calc_total,   
)

from .forms import DishForm
from .models import (
    MasterClass, Schedule, Booking, Hall, Chef, Cuisine,
    Dish, PurchaseList, PurchaseItem,
)
from .services import book_station, generate_purchase_list

logger = logging.getLogger(__name__)

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

    q = request.GET.get("q", "").strip()
    if q:
        for word in q.split():
            qs = qs.filter(
                Q(title__icontains=word)
                | Q(description__icontains=word)
                | Q(cuisine__name__icontains=word)
            )

    cuisine = request.GET.get("cuisine")
    if cuisine:
        qs = qs.filter(cuisine__name=cuisine)

    chef = request.GET.get("chef")
    if chef:
        qs = qs.filter(schedules__chef_id=chef).distinct()

    date = request.GET.get("date")
    if date:
        
        qs = qs.filter(schedules__start_datetime__date=date).distinct()

    sort = request.GET.get("sort")
    if sort == "price":
        qs = qs.order_by("adult_price", "title")
    elif sort == "date":
        qs = qs.order_by("schedules__start_datetime", "title").distinct()
    else:
        qs = qs.order_by("title")

    context = {
        "workshops": qs,
        "cuisines": Cuisine.objects.values_list("name", "name"),
        "chefs": Chef.objects.all(),
        "total": qs.count(),
    }

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

@login_required
def booking_create(request, session_id):
    schedule = get_object_or_404(
        Schedule.objects.select_related("masterclass", "chef", "hall"),
        pk=session_id,
    )

    if request.method == "POST":
        ticket_type = request.POST.get("ticket_type", "single")
        
        logger.info(
            "Начало обработки брони: user=%s, session=%s, type=%s",
            request.user.username, session_id, ticket_type
        )

        if ticket_type == "pair":
            portions = 2
        else:
            try:
                portions = max(1, min(10, int(request.POST.get("portions", 1))))
            except (TypeError, ValueError):
                
                logger.warning(
                    "Некорректное количество порций: user=%s, session=%s, raw_value=%s",
                    request.user.username, session_id, request.POST.get("portions")
                )
                portions = 1

        try:
            booking = book_station(request.user, schedule.id, ticket_type, portions)
            messages.success(request, f"Бронь оформлена: {booking.total} ₽")
            return redirect("cabinet")
        except ValidationError as e:
            
            logger.warning(
                "Ошибка бронирования: user=%s, session=%s, error=%s",
                request.user.username, session_id, e
            )
            messages.error(request, str(e))
            return redirect("booking", session_id=schedule.id)

    return render(request, "booking.html", {"session": schedule})

@login_required
@require_POST
def booking_edit(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)

    if booking.status == "cancelled":
        messages.error(request, "Отменённую бронь нельзя изменить.")
        return redirect("cabinet")

    new_type = request.POST.get("ticket_type")
    if new_type not in ("single", "pair"):
        messages.error(request, "Некорректный тип билета")
        return redirect("cabinet")


    if not booking_is_open(booking.schedule):
        messages.error(request, "Занятие уже закрыто для изменения брони.")
        return redirect("cabinet")

    booking.ticket_type = new_type
    booking.portions = 1
    booking.total = calc_total(booking.schedule.masterclass, new_type, 1)
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
        .select_related("schedule", "schedule__masterclass", "schedule__hall")
        .order_by("-id")
    )
    
    return render(request, "cabinet.html", {"bookings": bookings})

def api_session_seats(request, session_id):
    schedule = get_object_or_404(Schedule, pk=session_id)
    free = max(0, schedule.hall.station_count - occupied_seats(schedule))
    booking_open = booking_is_open(schedule)
    return JsonResponse({"free": free, "booking_open": booking_open})

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

def policy(request):
    return render(request, "policy.html")

def contacts(request):
    return render(request, "contacts.html")

@staff_member_required
def purchaser_list(request):
    sessions = (
        Schedule.objects
        .select_related("masterclass", "hall", "chef")
        .prefetch_related("purchase_list")
        .all()
    )
    total_portions = sum(
        s.purchase_list.total_portions for s in sessions if s.purchase_list
    )
    return render(request, "purchaser.html", {
        "sessions": sessions,
        "total_portions": total_portions,
    })


@staff_member_required
def dish_list(request):
    dishes = Dish.objects.all().order_by("-id")
    return render(request, "dish_list.html", {"dishes": dishes})


@staff_member_required
def dish_upload(request):
    if request.method == "POST":
        form = DishForm(request.POST, request.FILES)
        if form.is_valid():
            dish = form.save()
            logger.info("Блюдо загружено: id=%s, name=%s", dish.id, dish.name)
            messages.success(request, "Блюдо добавлено")
            return redirect("dish_list")
    else:
        form = DishForm()
    return render(request, "dish_upload.html", {"form": form})


# ---------- FR-15: Dashboard ----------
@staff_member_required
def dashboard(request):
    from django.db.models import Count, Sum, Avg, Q
    total_bookings = Booking.objects.filter(status__in=['active', 'paid']).count()
    revenue = Booking.objects.filter(status__in=['active', 'paid']).aggregate(s=Sum('total'))['s'] or 0
    avg_check = Booking.objects.filter(status__in=['active', 'paid']).aggregate(a=Avg('total'))['a'] or 0
    pair_count = Booking.objects.filter(ticket_type='pair', status__in=['active', 'paid']).count()
    pair_share = (pair_count / total_bookings * 100) if total_bookings else 0

    halls = (
        Booking.objects
        .filter(status__in=['active', 'paid'])
        .values("schedule__hall__name")
        .annotate(cnt=Count('id'))
        .order_by("-cnt")
    )

    context = {
        "total_bookings": total_bookings,
        "revenue": revenue,
        "avg_check": avg_check,
        "pair_share": round(pair_share, 1),
        "halls": halls,
    }
    return render(request, "dashboard.html", context)


# ---------- FR-16: Шеф видит участников своего занятия ----------
@staff_member_required
def session_participants(request, schedule_id):
    schedule = get_object_or_404(
        Schedule.objects.select_related("masterclass", "hall", "chef"),
        pk=schedule_id,
    )
    bookings = (
        schedule.bookings
        .filter(status__in=['active', 'paid'])
        .select_related("user")
        .order_by("-created_at")
    )
    return render(request, "session_participants.html", {
        "schedule": schedule,
        "bookings": bookings,
    })



@staff_member_required
def generate_purchase_view(request, schedule_id):
    generate_purchase_list(schedule_id)
    messages.success(request, "Закупочный лист сформирован")
    return redirect("purchaser")


@staff_member_required
def export_purchase_list_csv(request, schedule_id):
    pl = get_object_or_404(PurchaseList, schedule_id=schedule_id)
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter=';')
    writer.writerow(["Ингредиент", "Количество", "Единица"])
    for item in pl.items.select_related("ingredient"):
        writer.writerow([item.ingredient.name, item.total_amount, item.ingredient.unit])
    response = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="purchase_{schedule_id}.csv"'
    return response


class ChefLoginView(LoginView):
    template_name = "chef/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("chef_cabinet")


def chef_signup(request):
    if request.method == "POST":
        form = ChefSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Аккаунт шефа создан")
            return redirect("chef_cabinet")
    else:
        form = ChefSignUpForm()
    return render(request, "chef/signup.html", {"form": form})


def chef_logout(request):
    auth_logout(request)
    messages.success(request, "Вы вышли из кабинета шефа")
    return redirect("home")


@login_required
def chef_cabinet(request):
    """Шеф видит только свои занятия."""
    if not hasattr(request.user, "chef_profile"):
        messages.error(request, "У вашего аккаунта нет профиля шефа.")
        return redirect("home")

    chef = request.user.chef_profile
    sessions = (
        Schedule.objects
        .filter(chef=chef)
        .select_related("masterclass", "hall", "chef")
        .order_by("-start_datetime")
    )
    return render(request, "chef/cabinet.html", {
        "chef": chef,
        "sessions": sessions,
    })


@login_required
def chef_session_participants(request, schedule_id):
    """Шеф видит участников только своего занятия."""
    if not hasattr(request.user, "chef_profile"):
        return redirect("home")

    schedule = get_object_or_404(
        Schedule.objects.select_related("masterclass", "hall", "chef"),
        pk=schedule_id,
    )
    if schedule.chef_id != request.user.chef_profile.id:
        messages.error(request, "Это занятие ведёт другой шеф.")
        return redirect("chef_cabinet")

    bookings = (
        schedule.bookings
        .filter(status__in=["active", "paid"])
        .select_related("user")
        .order_by("-created_at")
    )
    return render(request, "chef/session_participants.html", {
        "schedule": schedule,
        "bookings": bookings,
    })