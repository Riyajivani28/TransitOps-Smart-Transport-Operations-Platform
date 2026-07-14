from django.shortcuts import redirect
from django.contrib import messages

def role_required(*roles):
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            user_role = None
            if hasattr(request.user, 'profile') and request.user.profile:
                user_role = request.user.profile.role
            
            # Superuser and Admin role always get unrestricted access
            if request.user.is_superuser or user_role == 'Admin' or user_role in roles:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, f"Access denied. Your role '{user_role}' does not have permission to access this page.")
            
            if user_role == 'Admin':
                return redirect('admin_dashboard')
            else:
                return redirect('dashboard')
        return wrapped_view
    return decorator
