"""
Permission decorators and helpers for role-based access control.
Provides @role_required, @min_role_level, and @owner_or_role.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .utils import get_user_role_level

def role_required(roles):
    """
    Decorator to check if user has one of the required roles
    Usage: @role_required(['admin', 'superuser'])
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            try:
                user_role = request.user.role.role
                if user_role in roles:
                    return view_func(request, *args, **kwargs)
            except:
                pass
            
            messages.error(request, "You don't have permission to access this page.")
            return redirect('dashboard')
        return wrapper
    return decorator

def min_role_level(level):
    """
    Decorator to check if user has minimum role level
    Usage: @min_role_level(2)  # Requires Staff or higher
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            user_level = get_user_role_level(request.user)
            if user_level >= level:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, "You don't have permission to access this page.")
            return redirect('dashboard')
        return wrapper
    return decorator

def owner_or_role(model_class, pk_param='pk', min_level=4):
    """
    Decorator to check if user is owner of object or has minimum role level
    Usage: @owner_or_role(Invoice, 'pk', 3)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            obj_id = kwargs.get(pk_param)
            try:
                obj = model_class.objects.get(pk=obj_id)
                
                # Check if user is owner (has created_by field)
                if hasattr(obj, 'created_by') and obj.created_by == request.user:
                    return view_func(request, *args, **kwargs)
                
                # Check role level
                user_level = get_user_role_level(request.user)
                if user_level >= min_level:
                    return view_func(request, *args, **kwargs)
                
            except model_class.DoesNotExist:
                messages.error(request, "Object not found.")
                return redirect('dashboard')
            
            messages.error(request, "You don't have permission to access this object.")
            return redirect('dashboard')
        return wrapper
    return decorator
