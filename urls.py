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
    path('signup/', auth_views.LoginView.as_view(template_name='login.html'), name='signup'),
]