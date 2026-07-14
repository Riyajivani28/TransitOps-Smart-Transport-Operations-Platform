from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Driver
from .forms import DriverForm
from accounts.decorators import role_required

@role_required('Dispatcher', 'Safety Officer')
def driver_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    cat_filter = request.GET.get('category', '')
    sort_by = request.GET.get('sort', 'name')

    drivers_list = Driver.objects.all()

    # Search
    if query:
        drivers_list = drivers_list.filter(
            Q(name__icontains=query) |
            Q(license_number__icontains=query) |
            Q(email__icontains=query)
        )

    # Filter
    if status_filter:
        drivers_list = drivers_list.filter(status=status_filter)
    if cat_filter:
        drivers_list = drivers_list.filter(license_category=cat_filter)

    # Sort
    if sort_by in ['name', '-name', 'safety_score', '-safety_score', 'license_expiry_date', '-license_expiry_date']:
        drivers_list = drivers_list.order_by(sort_by)
    else:
        drivers_list = drivers_list.order_by('name')

    # Pagination
    paginator = Paginator(drivers_list, 6) # 6 drivers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'cat_filter': cat_filter,
        'sort_by': sort_by,
        'status_choices': Driver.STATUS_CHOICES,
        'category_choices': Driver.LICENSE_CATEGORY_CHOICES
    }
    return render(request, 'drivers/list.html', context)

@role_required('Dispatcher', 'Safety Officer')
def driver_create(request):
    if request.method == 'POST':
        form = DriverForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Driver registered successfully!")
            return redirect('driver_list')
        else:
            messages.error(request, "Error registering driver. Please verify fields.")
    else:
        form = DriverForm()
    return render(request, 'drivers/form.html', {'form': form, 'title': 'Register Driver'})

@role_required('Dispatcher', 'Safety Officer')
def driver_detail(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    trips = driver.trips.all().order_by('-start_date')[:5]
    return render(request, 'drivers/detail.html', {'driver': driver, 'trips': trips})

@role_required('Dispatcher', 'Safety Officer')
def driver_update(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == 'POST':
        form = DriverForm(request.POST, request.FILES, instance=driver)
        if form.is_valid():
            form.save()
            messages.success(request, "Driver updated successfully!")
            return redirect('driver_detail', pk=pk)
        else:
            messages.error(request, "Error updating driver. Please verify fields.")
    else:
        form = DriverForm(instance=driver)
    return render(request, 'drivers/form.html', {'form': form, 'title': 'Edit Driver', 'driver': driver})

@role_required('Dispatcher', 'Safety Officer')
def driver_delete(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == 'POST':
        driver.delete()
        messages.success(request, "Driver removed successfully!")
        return redirect('driver_list')
    return render(request, 'drivers/confirm_delete.html', {'driver': driver})
