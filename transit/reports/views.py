from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, Avg, Count, F
import csv
import json

from vehicles.models import Vehicle
from drivers.models import Driver
from trips.models import Trip
from maintenance.models import Maintenance
from fuel.models import FuelLog
from expenses.models import Expense

@login_required
def reports_home(request):
    report_type = request.GET.get('type', 'operational_cost')
    
    user_role = getattr(request.user.profile, 'role', None) if hasattr(request.user, 'profile') else None
    if user_role == 'Fleet Manager' and report_type == 'driver_performance':
        report_type = 'operational_cost'
        
    # 1. Operational Cost Report Data
    op_cost_data = Expense.objects.values('expense_type').annotate(total=Sum('amount'))
    op_labels = [item['expense_type'] for item in op_cost_data]
    op_values = [float(item['total']) for item in op_cost_data]

    # 2. Fuel Cost Report Data
    fuel_cost_data = FuelLog.objects.values('vehicle__registration_number').annotate(total_cost=Sum('cost'), total_liters=Sum('liters'))
    fuel_labels = [item['vehicle__registration_number'] for item in fuel_cost_data]
    fuel_values = [float(item['total_cost']) for item in fuel_cost_data]

    # 3. Maintenance Cost Report Data
    maint_cost_data = Maintenance.objects.values('vehicle__registration_number').annotate(total_cost=Sum('cost'))
    maint_labels = [item['vehicle__registration_number'] for item in maint_cost_data]
    maint_values = [float(item['total_cost']) for item in maint_cost_data]

    # 4. Vehicle ROI Data (Acquisition Cost vs Operational Expenses)
    vehicles = Vehicle.objects.all()
    roi_labels = []
    roi_acquisition = []
    roi_expenses = []
    for v in vehicles:
        roi_labels.append(v.registration_number)
        roi_acquisition.append(float(v.acquisition_cost))
        total_exp = Expense.objects.filter(vehicle=v).aggregate(total=Sum('amount'))['total'] or 0
        roi_expenses.append(float(total_exp))

    # 5. Driver Performance
    drivers = Driver.objects.all().order_by('-safety_score')
    driver_labels = [d.name for d in drivers]
    driver_scores = [d.safety_score for d in drivers]

    # Prepare context data
    context = {
        'report_type': report_type,
        
        # Operational Cost context
        'op_cost_data': op_cost_data,
        'op_chart_json': json.dumps({'labels': op_labels, 'data': op_values}),
        
        # Fuel context
        'fuel_cost_data': fuel_cost_data,
        'fuel_chart_json': json.dumps({'labels': fuel_labels, 'data': fuel_values}),
        
        # Maintenance context
        'maint_cost_data': maint_cost_data,
        'maint_chart_json': json.dumps({'labels': maint_labels, 'data': maint_values}),
        
        # ROI context
        'roi_labels_json': json.dumps(roi_labels),
        'roi_acquisition_json': json.dumps(roi_acquisition),
        'roi_expenses_json': json.dumps(roi_expenses),
        'vehicles_roi_list': zip(roi_labels, roi_acquisition, roi_expenses),
        
        # Driver Performance context
        'drivers_list': drivers,
        'driver_chart_json': json.dumps({'labels': driver_labels, 'data': driver_scores}),
    }
    
    return render(request, 'reports/index.html', context)

@login_required
def export_report_csv(request, report_type):
    user_role = getattr(request.user.profile, 'role', None) if hasattr(request.user, 'profile') else None
    if user_role == 'Fleet Manager' and report_type in ['driver_performance', 'trip_history']:
        return HttpResponse("Access Denied: You do not have permission to export this report.", status=403)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="transitops_{report_type}_report.csv"'
    writer = csv.writer(response)

    if report_type == 'operational_cost':
        writer.writerow(['Expense Type', 'Total Amount (INR)'])
        data = Expense.objects.values('expense_type').annotate(total=Sum('amount'))
        for row in data:
            writer.writerow([row['expense_type'], row['total']])
            
    elif report_type == 'fuel_cost':
        writer.writerow(['Vehicle Registration', 'Total Liters', 'Total Cost (INR)'])
        data = FuelLog.objects.values('vehicle__registration_number').annotate(total_cost=Sum('cost'), total_liters=Sum('liters'))
        for row in data:
            writer.writerow([row['vehicle__registration_number'], row['total_liters'], row['total_cost']])
            
    elif report_type == 'maintenance':
        writer.writerow(['Vehicle Registration', 'Total Maintenance Cost (INR)'])
        data = Maintenance.objects.values('vehicle__registration_number').annotate(total_cost=Sum('cost'))
        for row in data:
            writer.writerow([row['vehicle__registration_number'], row['total_cost']])
            
    elif report_type == 'roi':
        writer.writerow(['Vehicle Registration', 'Acquisition Cost (INR)', 'Total Operational Expenses (INR)'])
        vehicles = Vehicle.objects.all()
        for v in vehicles:
            total_exp = Expense.objects.filter(vehicle=v).aggregate(total=Sum('amount'))['total'] or 0
            writer.writerow([v.registration_number, v.acquisition_cost, total_exp])
            
    elif report_type == 'driver_performance':
        writer.writerow(['Driver Name', 'License Number', 'Safety Score (0-100)', 'Status'])
        drivers = Driver.objects.all()
        for d in drivers:
            writer.writerow([d.name, d.license_number, d.safety_score, d.status])
            
    elif report_type == 'trip_history':
        writer.writerow(['Trip Number', 'Source', 'Destination', 'Vehicle', 'Driver', 'Cargo Weight (kg)', 'Status', 'Start Date'])
        trips = Trip.objects.all().order_by('-start_date')
        for t in trips:
            writer.writerow([t.trip_number, t.source, t.destination, t.vehicle.registration_number, t.driver.name, t.cargo_weight, t.status, t.start_date.strftime('%Y-%m-%d %H:%M')])
            
    else:
        writer.writerow(['No data available for this report type.'])

    return response
