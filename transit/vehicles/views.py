from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Vehicle
from .forms import VehicleForm

@login_required
def vehicle_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')
    sort_by = request.GET.get('sort', 'name')

    vehicles_list = Vehicle.objects.all()

    # Search
    if query:
        vehicles_list = vehicles_list.filter(
            Q(registration_number__icontains=query) |
            Q(name__icontains=query) |
            Q(model__icontains=query)
        )

    # Filter
    if status_filter:
        vehicles_list = vehicles_list.filter(status=status_filter)
    if type_filter:
        vehicles_list = vehicles_list.filter(vehicle_type=type_filter)

    # Sort
    if sort_by in ['name', '-name', 'registration_number', '-registration_number', 'current_odometer', '-current_odometer', 'acquisition_cost', '-acquisition_cost']:
        vehicles_list = vehicles_list.order_by(sort_by)
    else:
        vehicles_list = vehicles_list.order_by('name')

    # Pagination
    paginator = Paginator(vehicles_list, 6) # 6 vehicles per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'sort_by': sort_by,
        'status_choices': Vehicle.STATUS_CHOICES,
        'type_choices': Vehicle.VEHICLE_TYPE_CHOICES
    }
    return render(request, 'vehicles/list.html', context)

@login_required
def vehicle_create(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehicle registered successfully!")
            return redirect('vehicle_list')
        else:
            messages.error(request, "Error registering vehicle. Please verify the fields.")
    else:
        form = VehicleForm()
    return render(request, 'vehicles/form.html', {'form': form, 'title': 'Register Vehicle'})

@login_required
def vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    # Get associated trips and maintenance
    trips = vehicle.trips.all().order_by('-start_date')[:5]
    maintenances = vehicle.maintenances.all().order_by('-start_date')[:5]
    return render(request, 'vehicles/detail.html', {
        'vehicle': vehicle,
        'trips': trips,
        'maintenances': maintenances
    })

@login_required
def vehicle_update(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        form = VehicleForm(request.POST, request.FILES, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehicle details updated successfully!")
            return redirect('vehicle_detail', pk=pk)
        else:
            messages.error(request, "Error updating vehicle. Please verify the fields.")
    else:
        form = VehicleForm(instance=vehicle)
    return render(request, 'vehicles/form.html', {'form': form, 'title': 'Edit Vehicle', 'vehicle': vehicle})

@login_required
def vehicle_delete(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        vehicle.delete()
        messages.success(request, "Vehicle deleted successfully!")
        return redirect('vehicle_list')
    return render(request, 'vehicles/confirm_delete.html', {'vehicle': vehicle})
