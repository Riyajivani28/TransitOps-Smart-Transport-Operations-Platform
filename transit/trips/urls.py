from django.urls import path
from . import views

urlpatterns = [
    path('', views.trip_list, name='trip_list'),
    path('add/', views.trip_create, name='trip_create'),
    path('dispatcher/create/', views.dispatcher_trip_create, name='dispatcher_trip_create'),
    path('<int:pk>/', views.trip_detail, name='trip_detail'),
    path('<int:pk>/edit/', views.trip_update, name='trip_update'),
    path('<int:pk>/delete/', views.trip_delete, name='trip_delete'),
    path('<int:pk>/status/<str:status>/', views.trip_status_change, name='trip_status_change'),
    path('<int:pk>/complete/', views.trip_complete_dispatcher, name='trip_complete_dispatcher'),
]
