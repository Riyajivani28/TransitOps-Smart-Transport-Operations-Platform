from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Trip
from .forms import TripForm, DispatcherTripForm
from vehicles.models import Vehicle
from drivers.models import Driver
from accounts.decorators import role_required

def sync_trip_statuses(trip):
    vehicle = trip.vehicle
    driver = trip.driver

    if trip.status == 'Dispatched':
        vehicle.status = 'On Trip'
        driver.status = 'On Trip'
    elif trip.status in ['Completed', 'Cancelled']:
        # Free them up if they were on this trip
        if vehicle.status == 'On Trip':
            vehicle.status = 'Available'
        if driver.status == 'On Trip':
            driver.status = 'Available'
    elif trip.status == 'Draft':
        # Ensure they are available
        if vehicle.status == 'On Trip':
            # Check if this vehicle is assigned to another dispatched trip
            if not Trip.objects.filter(vehicle=vehicle, status='Dispatched').exclude(pk=trip.pk).exists():
                vehicle.status = 'Available'
        if driver.status == 'On Trip':
            if not Trip.objects.filter(driver=driver, status='Dispatched').exclude(pk=trip.pk).exists():
                driver.status = 'Available'

    vehicle.save()
    driver.save()

@role_required('Dispatcher', 'Safety Officer')
def trip_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    sort_by = request.GET.get('sort', '-start_date')

    trips_list = Trip.objects.all()

    # Search
    if query:
        trips_list = trips_list.filter(
            Q(trip_number__icontains=query) |
            Q(source__icontains=query) |
            Q(destination__icontains=query) |
            Q(vehicle__name__icontains=query) |
            Q(driver__name__icontains=query)
        )

    # Filter
    if status_filter:
        trips_list = trips_list.filter(status=status_filter)

    # Sort
    if sort_by in ['trip_number', '-trip_number', 'start_date', '-start_date', 'cargo_weight', '-cargo_weight']:
        trips_list = trips_list.order_by(sort_by)
    else:
        trips_list = trips_list.order_by('-start_date')

    # Pagination
    paginator = Paginator(trips_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'status_choices': Trip.STATUS_CHOICES
    }
    return render(request, 'trips/list.html', context)

@role_required('Dispatcher', 'Safety Officer')
def trip_create(request):
    if request.method == 'POST':
        form = TripForm(request.POST)
        if form.is_valid():
            trip = form.save()
            sync_trip_statuses(trip)
            messages.success(request, f"Trip {trip.trip_number} created successfully!")
            return redirect('trip_list')
        else:
            messages.error(request, "Error creating trip. Check form details.")
    else:
        form = TripForm()
    return render(request, 'trips/form.html', {'form': form, 'title': 'Create Trip'})

@role_required('Dispatcher', 'Safety Officer')
def trip_detail(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    # Check if vehicle has fuel logs for this trip
    fuel_logs = trip.fuel_logs.all()
    return render(request, 'trips/detail.html', {'trip': trip, 'fuel_logs': fuel_logs})

@role_required('Dispatcher', 'Safety Officer')
def trip_update(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    old_vehicle = trip.vehicle
    old_driver = trip.driver
    
    if request.method == 'POST':
        form = TripForm(request.POST, instance=trip)
        if form.is_valid():
            # If vehicle/driver changed, revert old ones to Available first
            new_trip = form.save(commit=False)
            if new_trip.vehicle != old_vehicle:
                old_vehicle.status = 'Available'
                old_vehicle.save()
            if new_trip.driver != old_driver:
                old_driver.status = 'Available'
                old_driver.save()
                
            new_trip.save()
            sync_trip_statuses(new_trip)
            messages.success(request, f"Trip {new_trip.trip_number} updated successfully!")
            return redirect('trip_detail', pk=pk)
        else:
            messages.error(request, "Error updating trip. Check form details.")
    else:
        form = TripForm(instance=trip)
    return render(request, 'trips/form.html', {'form': form, 'title': 'Edit Trip', 'trip': trip})

@role_required('Dispatcher', 'Safety Officer')
def trip_delete(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if request.method == 'POST':
        # Free up vehicle and driver
        vehicle = trip.vehicle
        driver = trip.driver
        vehicle.status = 'Available'
        driver.status = 'Available'
        vehicle.save()
        driver.save()
        
        trip.delete()
        messages.success(request, "Trip deleted successfully!")
        return redirect('trip_list')
    return render(request, 'trips/confirm_delete.html', {'trip': trip})

@role_required('Dispatcher', 'Safety Officer')
def trip_status_change(request, pk, status):
    trip = get_object_or_404(Trip, pk=pk)
    if status in ['Draft', 'Dispatched', 'Completed', 'Cancelled']:
        trip.status = status
        trip.save()
        sync_trip_statuses(trip)
        messages.success(request, f"Trip {trip.trip_number} status updated to {status}.")
    else:
        messages.error(request, "Invalid status choice.")
    return redirect('trip_detail', pk=pk)

@role_required('Dispatcher')
def trip_complete_dispatcher(request, pk):
    from django.utils import timezone
    from fuel.models import FuelLog
    from expenses.models import Expense

    trip = get_object_or_404(Trip, pk=pk)
    
    if trip.status != 'Dispatched':
        messages.error(request, "Only dispatched trips can be completed.")
        return redirect('dispatcher_dashboard')
        
    if request.method == 'POST':
        final_odometer = request.POST.get('final_odometer')
        fuel_used = request.POST.get('fuel_used')
        fuel_cost = request.POST.get('fuel_cost')
        fuel_station = request.POST.get('fuel_station', 'HP Pump')
        
        # Simple Validation
        if not final_odometer or not fuel_used or not fuel_cost:
            messages.error(request, "All fields (Final Odometer, Fuel Used, Fuel Cost) are required.")
            return render(request, 'trips/complete_trip.html', {'trip': trip})
            
        try:
            final_odometer = float(final_odometer)
            fuel_used = float(fuel_used)
            fuel_cost = float(fuel_cost)
        except ValueError:
            messages.error(request, "Invalid numeric values entered.")
            return render(request, 'trips/complete_trip.html', {'trip': trip})
            
        vehicle = trip.vehicle
        if final_odometer < float(vehicle.current_odometer):
            messages.error(request, f"Final odometer cannot be less than the current odometer ({vehicle.current_odometer} km).")
            return render(request, 'trips/complete_trip.html', {'trip': trip})
            
        # Update trip status
        trip.status = 'Completed'
        trip.end_date = timezone.now()
        trip.save()
        
        # Update vehicle status and odometer
        vehicle.current_odometer = final_odometer
        vehicle.status = 'Available'
        vehicle.save()
        
        # Update driver status
        driver = trip.driver
        driver.status = 'Available'
        driver.save()
        
        # Create FuelLog
        FuelLog.objects.create(
            vehicle=vehicle,
            trip=trip,
            fuel_date=timezone.now().date(),
            liters=fuel_used,
            cost=fuel_cost,
            fuel_station=fuel_station or 'HP Pump',
            notes=f"Logged automatically on completion of Trip {trip.trip_number}"
        )
        
        # Create Expense
        Expense.objects.create(
            vehicle=vehicle,
            expense_type='Fuel',
            amount=fuel_cost,
            expense_date=timezone.now().date(),
            remarks=f"Fuel Log: {fuel_used} Liters at {fuel_station} (Trip {trip.trip_number})"
        )
        
        messages.success(request, f"Trip {trip.trip_number} completed successfully. Vehicle and Driver are now Available.")
        return redirect('dispatcher_dashboard')
        
    return render(request, 'trips/complete_trip.html', {'trip': trip})


@role_required('Dispatcher')
def dispatcher_trip_create(request):
    """Dedicated trip-creation view for the Dispatcher Dashboard.
    Uses the simplified DispatcherTripForm (source, destination, vehicle, driver, cargo_weight).
    trip_number and start_date are auto-generated.
    """
    import uuid as uuid_module
    from django.utils import timezone as tz

    if request.method == 'POST':
        form = DispatcherTripForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            # Auto-generate a short unique trip number
            trip_number = 'TRP-' + uuid_module.uuid4().hex[:6].upper()
            # Ensure uniqueness
            while Trip.objects.filter(trip_number=trip_number).exists():
                trip_number = 'TRP-' + uuid_module.uuid4().hex[:6].upper()

            trip = Trip.objects.create(
                trip_number=trip_number,
                source=cd['source'],
                destination=cd['destination'],
                vehicle=cd['vehicle'],
                driver=cd['driver'],
                cargo_weight=cd['cargo_weight'],
                expected_distance=0,   # not required by dispatcher flow
                start_date=tz.now(),
                status='Draft',
            )
            messages.success(request, f'Trip {trip.trip_number} created! Ready to dispatch.')
            return redirect('dispatcher_dashboard')
        else:
            messages.error(request, 'Please fix the errors below before creating the trip.')
    else:
        form = DispatcherTripForm()

    import json
    vehicles_data = {str(v.pk): float(v.max_load_capacity) for v in Vehicle.objects.filter(status='Available')}

    return render(request, 'trips/dispatcher_create_trip.html', {
        'form': form,
        'available_vehicles': Vehicle.objects.filter(status='Available'),
        'vehicle_capacities_json': json.dumps(vehicles_data),
    })
