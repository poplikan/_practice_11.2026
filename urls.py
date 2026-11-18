from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog/', views.catalog, name='catalog'),
    path('catalog/<int:pk>/', views.workshop_detail, name='workshop_detail'),
    path('booking/<int:session_id>/', views.booking_create, name='booking'),
    path('cabinet/', views.cabinet, name='cabinet'),
    path('purchaser/', views.purchaser_list, name='purchaser'),
    path('policy/', views.policy, name='policy'),
    path('contacts/', views.contacts, name='contacts'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('signup/', auth_views.LoginView.as_view(template_name='signup.html'), name='signup'),
    path('api/sessions/<int:session_id>/seats/', views.api_session_seats, name='api_session_seats'),
    path('password-change/', auth_views.PasswordChangeView.as_view(template_name='password_change.html', success_url='/cabinet/'), name='password_change'),
    path(
    'booking/<int:booking_id>/edit/',
    views.booking_edit,
    name='booking_edit'
    ),
    path(
        'booking/<int:booking_id>/cancel/',
        views.booking_cancel,
        name='booking_cancel'
    ),
]
