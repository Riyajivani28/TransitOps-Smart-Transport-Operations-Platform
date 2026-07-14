from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard'),
    path('fleet-manager/', views.fleet_manager_dashboard, name='fleet_manager_dashboard'),
    path('dispatcher/', views.dispatcher_dashboard, name='dispatcher_dashboard'),
    path('safety/', views.safety_dashboard, name='safety_dashboard'),
    path('safety/export/', views.export_safety_pdf, name='export_safety_pdf'),
    path('finance/', views.finance_dashboard, name='finance_dashboard'),
    path('finance/export/', views.export_finance_csv, name='export_finance_csv'),
]
