from django.urls import path
from . import views

urlpatterns = [
    path('', views.fuel_list, name='fuel_list'),
    path('add/', views.fuel_create, name='fuel_create'),
    path('<int:pk>/edit/', views.fuel_update, name='fuel_update'),
    path('<int:pk>/delete/', views.fuel_delete, name='fuel_delete'),
]
