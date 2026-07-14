from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponse
from datetime import datetime, timedelta
import json
import csv

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from vehicles.models import Vehicle
from drivers.models import Driver
from trips.models import Trip
from maintenance.models import Maintenance
from fuel.models import FuelLog
from expenses.models import Expense
from accounts.decorators import role_required

@login_required
def dashboard_home(request):
    if hasattr(request.user, 'profile') and request.user.profile.role == 'Admin':
        return redirect('admin_dashboard')
    if hasattr(request.user, 'profile') and request.user.profile.role == 'Fleet Manager':
        return redirect('fleet_manager_dashboard')
    if hasattr(request.user, 'profile') and request.user.profile.role == 'Dispatcher':
        return redirect('dispatcher_dashboard')
    if hasattr(request.user, 'profile') and request.user.profile.role == 'Safety Officer':
        return redirect('safety_dashboard')
    if hasattr(request.user, 'profile') and request.user.profile.role == 'Financial Analyst':
        return redirect('finance_dashboard')
        
    # --- KPI calculations ---
    total_vehicles = Vehicle.objects.count()
    active_vehicles_count = Vehicle.objects.exclude(status='Retired').count()
    available_vehicles = Vehicle.objects.filter(status='Available').count()
    vehicles_on_trip = Vehicle.objects.filter(status='On Trip').count()
    vehicles_in_shop = Vehicle.objects.filter(status='In Shop').count()
    retired_vehicles = Vehicle.objects.filter(status='Retired').count()

    drivers_available = Driver.objects.filter(status='Available').count()
    drivers_on_trip = Driver.objects.filter(status='On Trip').count()
    suspended_drivers = Driver.objects.filter(status='Suspended').count()
    drivers_off_duty = Driver.objects.filter(status='Off Duty').count()

    active_trips = Trip.objects.filter(status='Dispatched').count()
    pending_trips = Trip.objects.filter(status='Draft').count()
    completed_trips = Trip.objects.filter(status='Completed').count()

    fleet_utilization = 0
    if active_vehicles_count > 0:
        fleet_utilization = round((vehicles_on_trip / active_vehicles_count) * 100, 1)

    # --- Recent activity tables ---
    recent_trips = Trip.objects.all().order_by('-start_date')[:5]
    recent_maintenance = Maintenance.objects.all().order_by('-start_date')[:5]
    recent_fuel_logs = FuelLog.objects.all().order_by('-fuel_date')[:5]
    recent_expenses = Expense.objects.all().order_by('-expense_date')[:5]

    # --- Charts Data (JSON format for Chart.js) ---
    vehicle_status_data = {
        'labels': ['Available', 'On Trip', 'In Shop', 'Retired'],
        'data': [available_vehicles, vehicles_on_trip, vehicles_in_shop, retired_vehicles]
    }

    driver_status_data = {
        'labels': ['Available', 'On Trip', 'Off Duty', 'Suspended'],
        'data': [drivers_available, drivers_on_trip, drivers_off_duty, suspended_drivers]
    }

    expenses_by_type = Expense.objects.values('expense_type').annotate(total_amount=Sum('amount'))
    expense_chart_labels = []
    expense_chart_data = []
    for exp in expenses_by_type:
        expense_chart_labels.append(exp['expense_type'])
        expense_chart_data.append(float(exp['total_amount']))

    if not expense_chart_data:
        expense_chart_labels = ['Fuel', 'Maintenance', 'Toll', 'Parking', 'Insurance', 'Other']
        expense_chart_data = [0, 0, 0, 0, 0, 0]

    monthly_trips_data = []
    monthly_trips_labels = []
    today = timezone.now()
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=i*30)
        month_name = month_date.strftime('%B')
        trips_count = Trip.objects.filter(start_date__year=month_date.year, start_date__month=month_date.month).count()
        monthly_trips_labels.append(month_name)
        monthly_trips_data.append(trips_count)

    context = {
        'active_vehicles': active_vehicles_count,
        'available_vehicles': available_vehicles,
        'vehicles_on_trip': vehicles_on_trip,
        'vehicles_in_shop': vehicles_in_shop,
        'retired_vehicles': retired_vehicles,
        'drivers_available': drivers_available,
        'drivers_on_trip': drivers_on_trip,
        'suspended_drivers': suspended_drivers,
        'active_trips': active_trips,
        'pending_trips': pending_trips,
        'completed_trips': completed_trips,
        'fleet_utilization': fleet_utilization,
        
        'recent_trips': recent_trips,
        'recent_maintenance': recent_maintenance,
        'recent_fuel_logs': recent_fuel_logs,
        'recent_expenses': recent_expenses,
        
        'vehicle_status_json': json.dumps(vehicle_status_data),
        'driver_status_json': json.dumps(driver_status_data),
        'expense_chart_json': json.dumps({
            'labels': expense_chart_labels,
            'data': expense_chart_data
        }),
        'monthly_trips_json': json.dumps({
            'labels': monthly_trips_labels,
            'data': monthly_trips_data
        })
    }

    return render(request, 'dashboard/index.html', context)

@role_required('Fleet Manager')
def fleet_manager_dashboard(request):
    total_vehicles = Vehicle.objects.count()
    active_vehicles_count = Vehicle.objects.exclude(status='Retired').count()
    available_vehicles = Vehicle.objects.filter(status='Available').count()
    vehicles_on_trip = Vehicle.objects.filter(status='On Trip').count()
    vehicles_in_shop = Vehicle.objects.filter(status='In Shop').count()
    retired_vehicles = Vehicle.objects.filter(status='Retired').count()
    
    fleet_utilization = 0
    if active_vehicles_count > 0:
        fleet_utilization = round((vehicles_on_trip / active_vehicles_count) * 100, 1)
        
    upcoming_maintenance = Maintenance.objects.filter(status='Open').order_by('start_date')[:5]
    recent_maintenance = Maintenance.objects.all().order_by('-start_date')[:5]
    recent_vehicles = Vehicle.objects.all().order_by('-id')[:5]
    
    # Vehicle Status Chart
    vehicle_status_data = {
        'labels': ['Available', 'On Trip', 'In Shop', 'Retired'],
        'data': [available_vehicles, vehicles_on_trip, vehicles_in_shop, retired_vehicles]
    }
    
    context = {
        'total_vehicles': total_vehicles,
        'available_vehicles': available_vehicles,
        'vehicles_on_trip': vehicles_on_trip,
        'vehicles_in_shop': vehicles_in_shop,
        'retired_vehicles': retired_vehicles,
        'fleet_utilization': fleet_utilization,
        'upcoming_maintenance': upcoming_maintenance,
        'recent_maintenance': recent_maintenance,
        'recent_vehicles': recent_vehicles,
        'vehicle_status_json': json.dumps(vehicle_status_data),
    }
    return render(request, 'dashboard/fleet_manager_dashboard.html', context)

@role_required('Dispatcher')
def dispatcher_dashboard(request):
    total_trips = Trip.objects.count()
    draft_trips = Trip.objects.filter(status='Draft').count()
    active_trips_count = Trip.objects.filter(status='Dispatched').count()
    completed_trips = Trip.objects.filter(status='Completed').count()
    cancelled_trips = Trip.objects.filter(status='Cancelled').count()
    
    available_vehicles_count = Vehicle.objects.filter(status='Available').count()
    available_drivers_count = Driver.objects.filter(status='Available').count()
    
    dispatched_trips = Trip.objects.filter(status='Dispatched').order_by('-start_date')
    draft_trips_list = Trip.objects.filter(status='Draft').order_by('-start_date')
    
    context = {
        'total_trips': total_trips,
        'draft_trips': draft_trips,
        'active_trips_count': active_trips_count,
        'completed_trips': completed_trips,
        'cancelled_trips': cancelled_trips,
        'available_vehicles_count': available_vehicles_count,
        'available_drivers_count': available_drivers_count,
        'dispatched_trips': dispatched_trips,
        'draft_trips_list': draft_trips_list,
    }
    return render(request, 'dashboard/dispatcher_dashboard.html', context)

@role_required('Safety Officer')
def safety_dashboard(request):
    if request.method == 'POST':
        driver_id = request.POST.get('driver_id')
        action = request.POST.get('action')
        driver = get_object_or_404(Driver, id=driver_id)
        
        if action == 'suspend':
            driver.status = 'Suspended'
            driver.save()
            messages.success(request, f"Driver {driver.name} has been suspended.")
        elif action == 'activate':
            driver.status = 'Available'
            driver.save()
            messages.success(request, f"Driver {driver.name} has been activated.")
            
        return redirect('safety_dashboard')
        
    drivers = Driver.objects.all().order_by('name')
    today = timezone.now().date()
    
    total_drivers = drivers.count()
    suspended_drivers = drivers.filter(status='Suspended').count()
    
    expired_licenses = 0
    expiring_soon_licenses = 0
    for d in drivers:
        if d.license_expiry_date < today:
            expired_licenses += 1
        elif today <= d.license_expiry_date <= today + timezone.timedelta(days=30):
            expiring_soon_licenses += 1
            
    avg_safety_score = drivers.aggregate(avg_score=Avg('safety_score'))['avg_score'] or 0.0
    avg_safety_score = round(avg_safety_score, 1)
    
    context = {
        'drivers': drivers,
        'total_drivers': total_drivers,
        'suspended_drivers': suspended_drivers,
        'expired_licenses': expired_licenses,
        'expiring_soon_licenses': expiring_soon_licenses,
        'avg_safety_score': avg_safety_score,
        'today': today,
    }
    return render(request, 'dashboard/safety_dashboard.html', context)

@role_required('Safety Officer')
def export_safety_pdf(request):
    drivers = Driver.objects.all().order_by('name')
    today = timezone.now().date()
    
    total_drivers = drivers.count()
    suspended_drivers = drivers.filter(status='Suspended').count()
    
    expired_licenses = 0
    expiring_soon_licenses = 0
    for d in drivers:
        if d.license_expiry_date < today:
            expired_licenses += 1
        elif today <= d.license_expiry_date <= today + timezone.timedelta(days=30):
            expiring_soon_licenses += 1
            
    avg_safety_score = drivers.aggregate(avg_score=Avg('safety_score'))['avg_score'] or 0.0
    avg_safety_score = round(avg_safety_score, 1)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="TransitOps_Safety_Compliance_Report.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#475569'),
        spaceAfter=15
    )
    
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=6,
        spaceBefore=12
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )
    
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#1E293B')
    )
    
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=table_cell_style,
        fontName='Helvetica-Bold'
    )
    
    status_active_style = ParagraphStyle(
        'StatusActive',
        parent=table_cell_style,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#16A34A')
    )
    
    status_suspended_style = ParagraphStyle(
        'StatusSuspended',
        parent=table_cell_style,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#DC2626')
    )
    
    status_ontrip_style = ParagraphStyle(
        'StatusOnTrip',
        parent=table_cell_style,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#2563EB')
    )
    
    status_offduty_style = ParagraphStyle(
        'StatusOffDuty',
        parent=table_cell_style,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#475569')
    )

    stats_data = [
        [
            Paragraph("<b>Total Drivers:</b>", table_cell_bold),
            Paragraph(str(total_drivers), table_cell_style),
            Paragraph("<b>Suspended Drivers:</b>", table_cell_bold),
            Paragraph(str(suspended_drivers), table_cell_style),
        ],
        [
            Paragraph("<b>Expired Licenses:</b>", table_cell_bold),
            Paragraph(str(expired_licenses), table_cell_style),
            Paragraph("<b>Avg Safety Score:</b>", table_cell_bold),
            Paragraph(f"{avg_safety_score}%", table_cell_style),
        ]
    ]
    stats_table = Table(stats_data, colWidths=[120, 150, 120, 150])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    table_data = [[
        Paragraph("Driver Profile", table_header_style),
        Paragraph("License Details", table_header_style),
        Paragraph("License Expiration", table_header_style),
        Paragraph("Safety Score", table_header_style),
        Paragraph("Status", table_header_style)
    ]]
    
    for d in drivers:
        profile_text = f"<b>{d.name}</b><br/>{d.email}<br/>{d.phone}"
        profile_para = Paragraph(profile_text, table_cell_style)
        
        license_text = f"<b>{d.license_number}</b><br/>{d.get_license_category_display()}"
        license_para = Paragraph(license_text, table_cell_style)
        
        expiry_str = d.license_expiry_date.strftime('%Y-%m-%d')
        if d.is_license_expired:
            expiry_text = f"<font color='#DC2626'><b>{expiry_str} (Expired)</b></font>"
        elif today <= d.license_expiry_date <= today + timezone.timedelta(days=30):
            expiry_text = f"<font color='#D97706'><b>{expiry_str} (Expiring Soon)</b></font>"
        else:
            expiry_text = f"<font color='#16A34A'><b>{expiry_str}</b></font>"
        expiry_para = Paragraph(expiry_text, table_cell_style)
        
        score_color = '#16A34A' if d.safety_score >= 90 else ('#D97706' if d.safety_score >= 75 else '#DC2626')
        score_text = f"<font color='{score_color}'><b>{d.safety_score}%</b></font>"
        score_para = Paragraph(score_text, table_cell_style)
        
        if d.status == 'Available':
            status_para = Paragraph("Available", status_active_style)
        elif d.status == 'On Trip':
            status_para = Paragraph("On Trip", status_ontrip_style)
        elif d.status == 'Suspended':
            status_para = Paragraph("Suspended", status_suspended_style)
        else:
            status_para = Paragraph(d.status, status_offduty_style)
            
        table_data.append([
            profile_para,
            license_para,
            expiry_para,
            score_para,
            status_para
        ])

    col_widths = [140, 100, 120, 80, 100]
    drivers_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    table_styles = [
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
    ]
    
    for i in range(1, len(table_data)):
        bg_color = colors.HexColor('#F8FAFC') if i % 2 == 0 else colors.white
        table_styles.append(('BACKGROUND', (0, i), (-1, i), bg_color))
        
    drivers_table.setStyle(TableStyle(table_styles))

    story = []
    story.append(Paragraph("TRANSITOPS SAFETY COMPLIANCE REPORT", title_style))
    story.append(Paragraph(f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')} | Confidential Fleet Audit Log", subtitle_style))
    story.append(Paragraph("Compliance Overview", section_title))
    story.append(stats_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph("Driver Registry Status", section_title))
    story.append(drivers_table)
    
    doc.build(story)
    return response

@role_required('Financial Analyst')
def finance_dashboard(request):
    fuel_logs = FuelLog.objects.all().order_by('-fuel_date')
    expenses = Expense.objects.all().order_by('-expense_date')
    
    total_fuel_cost = float(FuelLog.objects.aggregate(total=Sum('cost'))['total'] or 0.0)
    total_maintenance_cost = float(Maintenance.objects.aggregate(total=Sum('cost'))['total'] or 0.0)
    total_other_expenses = float(Expense.objects.exclude(expense_type='Fuel').aggregate(total=Sum('amount'))['total'] or 0.0)
    
    total_operational_cost = total_fuel_cost + total_maintenance_cost + total_other_expenses
    
    completed_trips = Trip.objects.filter(status='Completed')
    trip_efficiency_list = []
    for trip in completed_trips:
        logs = FuelLog.objects.filter(trip=trip)
        if logs.exists():
            total_liters = sum(log.liters for log in logs)
            if total_liters > 0:
                efficiency = float(trip.expected_distance) / float(total_liters)
                trip_efficiency_list.append(efficiency)
                
    avg_fuel_efficiency = sum(trip_efficiency_list) / len(trip_efficiency_list) if trip_efficiency_list else 0.0
    avg_fuel_efficiency = round(avg_fuel_efficiency, 2)
    
    vehicles = Vehicle.objects.all()
    vehicle_roi_data = []
    for v in vehicles:
        v_fuel = float(FuelLog.objects.filter(vehicle=v).aggregate(total=Sum('cost'))['total'] or 0.0)
        v_maint = float(Maintenance.objects.filter(vehicle=v).aggregate(total=Sum('cost'))['total'] or 0.0)
        v_other = float(Expense.objects.filter(vehicle=v).exclude(expense_type='Fuel').aggregate(total=Sum('amount'))['total'] or 0.0)
        v_op_cost = v_fuel + v_maint + v_other
        
        v_completed_trips = Trip.objects.filter(vehicle=v, status='Completed').count()
        v_revenue = v_completed_trips * 15000.00
        
        acq_cost = float(v.acquisition_cost)
        if acq_cost > 0:
            roi_percentage = ((v_revenue - float(v_op_cost)) / acq_cost) * 100
            roi_percentage = round(roi_percentage, 1)
        else:
            roi_percentage = 0.0
            
        vehicle_roi_data.append({
            'vehicle': v,
            'completed_trips': v_completed_trips,
            'op_cost': v_op_cost,
            'revenue': v_revenue,
            'roi_percentage': roi_percentage
        })
        
    context = {
        'fuel_logs': fuel_logs[:10],
        'expenses': expenses[:10],
        'total_fuel_cost': total_fuel_cost,
        'total_maintenance_cost': total_maintenance_cost,
        'total_operational_cost': total_operational_cost,
        'avg_fuel_efficiency': avg_fuel_efficiency,
        'vehicle_roi_data': vehicle_roi_data,
    }
    return render(request, 'dashboard/finance_dashboard.html', context)

@role_required('Financial Analyst')
def export_finance_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="TransitOps_Finance_Report.csv"'
    
    writer = csv.writer(response)
    
    writer.writerow(['TRANSITOPS FINANCIAL REPORT'])
    writer.writerow([])
    
    writer.writerow(['FUEL LOGS'])
    writer.writerow(['Vehicle', 'Fuel Date', 'Liters', 'Cost (INR)', 'Station', 'Notes'])
    for log in FuelLog.objects.all().order_by('-fuel_date'):
        writer.writerow([
            log.vehicle.registration_number,
            log.fuel_date,
            log.liters,
            log.cost,
            log.fuel_station,
            log.notes
        ])
        
    writer.writerow([])
    writer.writerow(['MAINTENANCE COSTS'])
    writer.writerow(['Vehicle', 'Start Date', 'End Date', 'Type', 'Description', 'Cost (INR)', 'Status'])
    for maint in Maintenance.objects.all().order_by('-start_date'):
        writer.writerow([
            maint.vehicle.registration_number,
            maint.start_date,
            maint.end_date or 'N/A',
            maint.maintenance_type,
            maint.description,
            maint.cost,
            maint.status
        ])
        
    writer.writerow([])
    writer.writerow(['EXPENSES'])
    writer.writerow(['Vehicle', 'Type', 'Amount (INR)', 'Date', 'Remarks'])
    for exp in Expense.objects.all().order_by('-expense_date'):
        writer.writerow([
            exp.vehicle.registration_number if exp.vehicle else 'Global/Fleet',
            exp.expense_type,
            exp.amount,
            exp.expense_date,
            exp.remarks
        ])
        
    return response

def error_404(request, exception):
    return render(request, 'errors/404.html', status=404)

def error_500(request):
    return render(request, 'errors/500.html', status=500)
