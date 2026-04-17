"""
Permission logic for role-based access control (Admin vs Client).
Includes queryset filtering and action-level permission checks.
"""
from .models import CustomerAssignment
from .utils import get_user_role_level

def has_permission(user, action, obj=None):
    """
    Check if user has permission to perform action
    action: 'create', 'read', 'update', 'delete'
    """
    role_level = get_user_role_level(user)
    
    # Admin (Level 2) can do anything
    if role_level >= 2:
        return True
    
    # General permissions by role
    if role_level == 1:  # Client
        return action == 'read'
    
    return False

def filter_invoices_by_role(user, queryset):
    """Filter invoice queryset based on user role"""
    role_level = get_user_role_level(user)
    
    # Admin (Level 2) sees all
    if role_level >= 2:
        return queryset
    
    # Clients (Level 1) see invoices for assigned customers
    assigned_customers = CustomerAssignment.objects.filter(user=user).values_list('customer_id', flat=True)
    return queryset.filter(customer_id__in=assigned_customers)

def filter_customers_by_role(user, queryset):
    """Filter customer queryset based on user role"""
    role_level = get_user_role_level(user)
    
    # Admin (Level 2) sees all
    if role_level >= 2:
        return queryset
    
    # Clients (Level 1) see assigned customers
    assigned_customers = CustomerAssignment.objects.filter(user=user).values_list('customer_id', flat=True)
    return queryset.filter(id__in=assigned_customers)

def can_delete_invoice(user, invoice):
    """Check if user can delete an invoice"""
    role_level = get_user_role_level(user)
    
    # Only Admin (Level 2) can delete any invoice
    if role_level >= 2:
        return True
    
    return False

def log_activity(user, action, obj, request=None, details=''):
    """Helper to log user activity"""
    from .models import ActivityLog
    
    ActivityLog.objects.create(
        user=user,
        action=action,
        model_name=obj.__class__.__name__,
        object_id=obj.pk if hasattr(obj, 'pk') else None,
        object_repr=str(obj),
        details=details
    )
