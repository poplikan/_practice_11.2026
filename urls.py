from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import (
    ChefLoginView, chef_signup, chef_logout, chef_cabinet,
    chef_session_participants,
)

urlpatterns = [
    # Публичные
    path("", views.home, name="home"),
    path("catalog/", views.catalog, name="catalog"),
    path("catalog/<int:pk>/", views.workshop_detail, name="workshop_detail"),
    path("policy/", views.policy, name="policy"),
    path("contacts/", views.contacts, name="contacts"),

    # Авторизация (участники)
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),
    path("signup/", views.signup, name="signup"),
    path("password-change/",
         auth_views.PasswordChangeView.as_view(
             template_name="password_change.html",
             success_url="/cabinet/",
         ),
         name="password_change"),

    # Личный кабинет участника
    path("cabinet/", views.cabinet, name="cabinet"),

    # Вход и регистрация для шефа
    path("chef/login/", ChefLoginView.as_view(), name="chef_login"),
    path("chef/signup/", chef_signup, name="chef_signup"),
    path("chef/logout/", chef_logout, name="chef_logout"),

    # Кабинет шефа
    path("chef/cabinet/", chef_cabinet, name="chef_cabinet"),
    path("chef/schedule/<int:schedule_id>/participants/",
         chef_session_participants, name="chef_session_participants"),

    # Бронирование
    path("booking/<int:session_id>/", views.booking_create, name="booking"),
    path("booking/<int:booking_id>/edit/", views.booking_edit, name="booking_edit"),
    path("booking/<int:booking_id>/cancel/", views.booking_cancel, name="booking_cancel"),

    # API
    path("api/sessions/<int:session_id>/seats/",
         views.api_session_seats, name="api_session_seats"),

    # FR-10: CRUD расписания (админ)
    path("schedule/", views.schedule_list, name="schedule_list"),
    path("schedule/<int:schedule_id>/edit/", views.session_edit, name="session_edit"),
    path("schedule/<int:schedule_id>/delete/", views.session_delete, name="session_delete"),
    path("schedule/<int:schedule_id>/participants/",
         views.session_participants, name="session_participants"),

    # Закупки (FR-07, FR-13)
    path("purchaser/", views.purchaser_list, name="purchaser"),
    path("purchaser/<int:schedule_id>/generate/",
         views.generate_purchase_view, name="generate_purchase"),
    path("purchaser/<int:schedule_id>/export.csv",
         views.export_purchase_list_csv, name="export_purchase_csv"),

    # Блюда (FR-12)
    path("dishes/", views.dish_list, name="dish_list"),
    path("dishes/upload/", views.dish_upload, name="dish_upload"),

    # Dashboard (FR-15)
    path("dashboard/", views.dashboard, name="dashboard"),
]