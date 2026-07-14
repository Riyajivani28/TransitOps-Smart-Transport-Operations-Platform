from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.db.models import Sum
from vehicles.models import Vehicle
from drivers.models import Driver
from trips.models import Trip
from fuel.models import FuelLog
from expenses.models import Expense
from .forms import UserLoginForm, ProfileUpdateForm, UserRegisterForm
from .models import Profile

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect(request.GET.get('next', 'dashboard'))
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = UserLoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

@login_required
def profile_view(request):
    # Ensure profile exists
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProfileUpdateForm(instance=profile)
        
    return render(request, 'accounts/profile.html', {'form': form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep the user logged in
            messages.success(request, "Password changed successfully!")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})

@login_required
def settings_view(request):
    if request.method == 'POST':
        dark_mode = request.POST.get('dark_mode') == 'true'
        email_notifications = request.POST.get('email_notifications') == 'true'
        
        # Save to session
        request.session['dark_mode'] = dark_mode
        request.session['email_notifications'] = email_notifications
        messages.success(request, "Settings updated successfully!")
        return redirect('settings')
        
    return render(request, 'accounts/settings.html')

def signup_view(request):
    return redirect('login')


def forgot_password_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username_or_email = request.POST.get('username_or_email')
        user = User.objects.filter(username=username_or_email).first() or User.objects.filter(email=username_or_email).first()
        if user:
            return redirect('reset_password_confirm', pk=user.pk)
        else:
            messages.error(request, "No account found with that username or email address.")
    return render(request, 'accounts/forgot_password.html')

def reset_password_confirm_view(request, pk):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if password == confirm_password:
            user.set_password(password)
            user.save()
            messages.success(request, "Password reset successful! You can now log in with your new password.")
            return redirect('login')
        else:
            messages.error(request, "Passwords do not match.")
    return render(request, 'accounts/reset_password_confirm.html', {'user_obj': user})

def admin_required(function=None, redirect_field_name=None, login_url='login'):
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and (u.is_superuser or (hasattr(u, 'profile') and u.profile.role == 'Admin')),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

@login_required
@admin_required
def admin_dashboard(request):
    total_users = User.objects.count()
    total_vehicles = Vehicle.objects.count()
    total_drivers = Driver.objects.count()
    total_trips = Trip.objects.count()
    
    vehicles_in_maintenance = Vehicle.objects.filter(status='In Shop').count()
    
    total_fuel_cost = FuelLog.objects.aggregate(total=Sum('cost'))['total'] or 0.0
    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0.0
    
    # Calculate fleet utilization
    vehicles_on_trip = Vehicle.objects.filter(status='On Trip').count()
    active_vehicles_count = Vehicle.objects.exclude(status='Retired').count()
    fleet_utilization = 0.0
    if active_vehicles_count > 0:
        fleet_utilization = round((vehicles_on_trip / active_vehicles_count) * 100, 1)

    recent_users = User.objects.all().order_by('-date_joined')[:5]

    context = {
        'total_users': total_users,
        'total_vehicles': total_vehicles,
        'total_drivers': total_drivers,
        'total_trips': total_trips,
        'vehicles_in_maintenance': vehicles_in_maintenance,
        'total_fuel_cost': total_fuel_cost,
        'total_expenses': total_expenses,
        'fleet_utilization': fleet_utilization,
        'recent_users': recent_users,
    }
    return render(request, 'accounts/admin_dashboard.html', context)

@login_required
@admin_required
def admin_user_list(request):
    users = User.objects.all().select_related('profile').order_by('id')
    return render(request, 'accounts/admin_user_list.html', {'users_list': users})

@login_required
@admin_required
def admin_role_list(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        new_role = request.POST.get('role')
        user_to_update = get_object_or_404(User, id=user_id)
        profile, created = Profile.objects.get_or_create(user=user_to_update)
        profile.role = new_role
        profile.save()
        messages.success(request, f"Updated role for {user_to_update.username} to {new_role} successfully!")
        return redirect('admin_role_list')
        
    users = User.objects.all().select_related('profile').order_by('id')
    role_choices = Profile.ROLE_CHOICES
    context = {
        'users_list': users,
        'role_choices': role_choices,
    }
    return render(request, 'accounts/admin_role_list.html', context)

@login_required
@admin_required
def admin_user_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        phone = request.POST.get('phone', '')
        
        if User.objects.filter(username=name).exists():
            messages.error(request, f"User with name '{name}' already exists.")
        else:
            user = User.objects.create_user(username=name, email=email, password=password)
            user.is_staff = True
            if role == 'Admin':
                user.is_superuser = True
            user.save()
            Profile.objects.create(user=user, role=role, phone=phone, raw_password=password)
            messages.success(request, f"User '{name}' created successfully with role '{role}'!")
            return redirect('admin_user_list')
            
    role_choices = Profile.ROLE_CHOICES
    return render(request, 'accounts/admin_user_create.html', {'role_choices': role_choices})

@login_required
@admin_required
def admin_user_edit(request, user_id):
    user_to_edit = get_object_or_404(User, id=user_id)
    profile, created = Profile.objects.get_or_create(user=user_to_edit)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        role = request.POST.get('role')
        phone = request.POST.get('phone', '')
        
        user_to_edit.username = name
        user_to_edit.email = email
        if role == 'Admin':
            user_to_edit.is_superuser = True
        else:
            user_to_edit.is_superuser = False
        user_to_edit.save()
        
        profile.role = role
        profile.phone = phone
        profile.save()
        
        messages.success(request, f"User '{name}' updated successfully!")
        return redirect('admin_user_list')
        
    role_choices = Profile.ROLE_CHOICES
    context = {
        'user_to_edit': user_to_edit,
        'profile': profile,
        'role_choices': role_choices,
    }
    return render(request, 'accounts/admin_user_edit.html', context)

@login_required
@admin_required
def admin_user_delete(request, user_id):
    user_to_delete = get_object_or_404(User, id=user_id)
    if user_to_delete == request.user:
        messages.error(request, "You cannot delete your own account.")
    else:
        username = user_to_delete.username
        user_to_delete.delete()
        messages.success(request, f"User '{username}' deleted successfully.")
    return redirect('admin_user_list')

@login_required
@admin_required
def admin_user_toggle_active(request, user_id):
    user_to_toggle = get_object_or_404(User, id=user_id)
    if user_to_toggle == request.user:
        messages.error(request, "You cannot deactivate your own account.")
    else:
        user_to_toggle.is_active = not user_to_toggle.is_active
        user_to_toggle.save()
        status_str = "activated" if user_to_toggle.is_active else "deactivated"
        messages.success(request, f"User '{user_to_toggle.username}' {status_str} successfully.")
    return redirect('admin_user_list')

@login_required
@admin_required
def admin_user_reset_password(request, user_id):
    user_to_reset = get_object_or_404(User, id=user_id)
    profile, created = Profile.objects.get_or_create(user=user_to_reset)
    
    if request.method == 'POST':
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if new_password == confirm_password:
            user_to_reset.set_password(new_password)
            user_to_reset.save()
            profile.raw_password = new_password
            profile.save()
            messages.success(request, f"Password reset for '{user_to_reset.username}' successful!")
            return redirect('admin_user_list')
        else:
            messages.error(request, "Passwords do not match.")
            
    return render(request, 'accounts/admin_user_reset_password.html', {'user_to_reset': user_to_reset})
