from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Публичные
    path('', views.home, name='home'),
    path('catalog/', views.catalog, name='catalog'),
    path('catalog/<int:pk>/', views.workshop_detail, name='workshop_detail'),
    path('policy/', views.policy, name='policy'),
    path('contacts/', views.contacts, name='contacts'),

    # Авторизация
    path('login/',  auth_views.LoginView.as_view(template_name='login.html'),  name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'),           name='logout'),
    path('signup/', views.signup,                                              name='signup'),
    path('password-change/',
         auth_views.PasswordChangeView.as_view(
             template_name='password_change.html',
             success_url='/cabinet/',
         ),
         name='password_change'),

    # Личный кабинет
    path('cabinet/', views.cabinet, name='cabinet'),

    # Бронирование
    path('booking/<int:session_id>/',        views.booking_create, name='booking'),
    path('booking/<int:booking_id>/edit/',   views.booking_edit,   name='booking_edit'),
    path('booking/<int:booking_id>/cancel/', views.booking_cancel, name='booking_cancel'),

    # API
    path('api/sessions/<int:session_id>/seats/',
         views.api_session_seats, name='api_session_seats'),

    # Админ-часть (если используете)
    path('purchaser/', views.purchaser_list, name='purchaser'),
]