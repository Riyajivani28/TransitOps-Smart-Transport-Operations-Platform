from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import FuelLog
from .forms import FuelLogForm
from expenses.models import Expense
from accounts.decorators import role_required

@role_required('Dispatcher', 'Financial Analyst')
def fuel_list(request):
    fuel_logs = FuelLog.objects.all().order_by('-fuel_date')
    
    # Calculate average efficiency
    total_liters = sum(log.liters for log in fuel_logs)
    total_cost = sum(log.cost for log in fuel_logs)
    
    paginator = Paginator(fuel_logs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'fuel/list.html', {
        'page_obj': page_obj,
        'total_liters': total_liters,
        'total_cost': total_cost,
    })

@role_required('Dispatcher', 'Financial Analyst')
def fuel_create(request):
    if request.method == 'POST':
        form = FuelLogForm(request.POST)
        if form.is_valid():
            fuel_log = form.save()
            
            # Sync to Expenses
            Expense.objects.create(
                vehicle=fuel_log.vehicle,
                expense_type='Fuel',
                amount=fuel_log.cost,
                expense_date=fuel_log.fuel_date,
                remarks=f"Fuel Log: {fuel_log.liters} Liters at {fuel_log.fuel_station}"
            )
            
            messages.success(request, f"Fuel log for {fuel_log.vehicle.registration_number} logged successfully.")
            return redirect('fuel_list')
        else:
            messages.error(request, "Error creating fuel log. Check inputs.")
    else:
        form = FuelLogForm()
    return render(request, 'fuel/form.html', {'form': form, 'title': 'Add Fuel Log'})

@role_required('Dispatcher', 'Financial Analyst')
def fuel_update(request, pk):
    fuel_log = get_object_or_404(FuelLog, pk=pk)
    old_cost = fuel_log.cost
    old_date = fuel_log.fuel_date
    old_vehicle = fuel_log.vehicle
    
    if request.method == 'POST':
        form = FuelLogForm(request.POST, instance=fuel_log)
        if form.is_valid():
            new_log = form.save()
            
            # Update expense record if exists
            exp = Expense.objects.filter(
                vehicle=old_vehicle,
                expense_type='Fuel',
                amount=old_cost,
                expense_date=old_date
            ).first()
            
            if exp:
                exp.vehicle = new_log.vehicle
                exp.amount = new_log.cost
                exp.expense_date = new_log.fuel_date
                exp.remarks = f"Fuel Log: {new_log.liters} Liters at {new_log.fuel_station}"
                exp.save()
            
            messages.success(request, "Fuel log updated successfully.")
            return redirect('fuel_list')
        else:
            messages.error(request, "Error updating fuel log.")
    else:
        form = FuelLogForm(instance=fuel_log)
    return render(request, 'fuel/form.html', {'form': form, 'title': 'Edit Fuel Log', 'fuel_log': fuel_log})

@role_required('Dispatcher', 'Financial Analyst')
def fuel_delete(request, pk):
    fuel_log = get_object_or_404(FuelLog, pk=pk)
    if request.method == 'POST':
        # Remove linked expense
        Expense.objects.filter(
            vehicle=fuel_log.vehicle,
            expense_type='Fuel',
            amount=fuel_log.cost,
            expense_date=fuel_log.fuel_date
        ).delete()
        
        fuel_log.delete()
        messages.success(request, "Fuel log deleted successfully.")
        return redirect('fuel_list')
    return render(request, 'fuel/confirm_delete.html', {'fuel_log': fuel_log})
