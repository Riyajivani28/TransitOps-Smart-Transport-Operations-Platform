from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Maintenance
from .forms import MaintenanceForm
from vehicles.models import Vehicle

def sync_maintenance_status(maint):
    vehicle = maint.vehicle
    if vehicle.status == 'Retired':
        return
        
    if maint.status == 'Open':
        vehicle.status = 'In Shop'
    elif maint.status == 'Closed':
        if vehicle.status == 'In Shop':
            vehicle.status = 'Available'
    vehicle.save()

@login_required
def maintenance_list(request):
    status_filter = request.GET.get('status', '')
    maintenances = Maintenance.objects.all().order_by('-start_date')

    if status_filter:
        maintenances = maintenances.filter(status=status_filter)

    paginator = Paginator(maintenances, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'maintenance/list.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'status_choices': Maintenance.STATUS_CHOICES
    })

@login_required
def maintenance_create(request):
    if request.method == 'POST':
        form = MaintenanceForm(request.POST)
        if form.is_valid():
            maint = form.save()
            sync_maintenance_status(maint)
            
            # Log as expense automatically
            from expenses.models import Expense
            Expense.objects.create(
                vehicle=maint.vehicle,
                expense_type='Maintenance',
                amount=maint.cost,
                expense_date=maint.start_date,
                remarks=f"Auto-generated from Maintenance Log: {maint.maintenance_type} - {maint.description}"
            )
            
            messages.success(request, f"Maintenance log for {maint.vehicle.registration_number} created.")
            return redirect('maintenance_list')
        else:
            messages.error(request, "Error creating maintenance log.")
    else:
        form = MaintenanceForm()
    return render(request, 'maintenance/form.html', {'form': form, 'title': 'Add Maintenance Log'})

@login_required
def maintenance_update(request, pk):
    maint = get_object_or_404(Maintenance, pk=pk)
    old_vehicle = maint.vehicle
    
    if request.method == 'POST':
        form = MaintenanceForm(request.POST, instance=maint)
        if form.is_valid():
            new_maint = form.save(commit=False)
            if new_maint.vehicle != old_vehicle:
                # Revert old vehicle status
                if old_vehicle.status == 'In Shop':
                    old_vehicle.status = 'Available'
                    old_vehicle.save()
            new_maint.save()
            sync_maintenance_status(new_maint)
            messages.success(request, "Maintenance log updated successfully.")
            return redirect('maintenance_list')
        else:
            messages.error(request, "Error updating maintenance log.")
    else:
        form = MaintenanceForm(instance=maint)
    return render(request, 'maintenance/form.html', {'form': form, 'title': 'Edit Maintenance Log', 'maint': maint})

@login_required
def maintenance_close(request, pk):
    maint = get_object_or_404(Maintenance, pk=pk)
    maint.status = 'Closed'
    maint.save()
    sync_maintenance_status(maint)
    messages.success(request, f"Maintenance log for {maint.vehicle.registration_number} closed.")
    return redirect('maintenance_list')

@login_required
def maintenance_delete(request, pk):
    maint = get_object_or_404(Maintenance, pk=pk)
    if request.method == 'POST':
        vehicle = maint.vehicle
        maint.delete()
        # Restore vehicle status if no other open maintenance exists
        if not Maintenance.objects.filter(vehicle=vehicle, status='Open').exists():
            if vehicle.status == 'In Shop':
                vehicle.status = 'Available'
                vehicle.save()
        messages.success(request, "Maintenance log deleted successfully.")
        return redirect('maintenance_list')
    return render(request, 'maintenance/confirm_delete.html', {'maint': maint})
