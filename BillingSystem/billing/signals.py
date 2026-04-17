"""
Django signals for the Billing app.
Handles audit logging (login/logout) and automated inventory management.
"""
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import ActivityLog

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log user login events"""
    ip = request.META.get('REMOTE_ADDR', 'Unknown IP')
    ActivityLog.objects.create(
        user=user,
        action='LOGIN',
        model_name='Auth',
        object_repr='User Session',
        details=f"User logged in from IP: {ip}"
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout events"""
    ip = request.META.get('REMOTE_ADDR', 'Unknown IP')
    ActivityLog.objects.create(
        user=user,
        action='LOGOUT',
        model_name='Auth',
        object_repr='User Session',
        details=f"User logged out from IP: {ip}"
    )

# --- Inventory Signals ---
from django.db.models.signals import post_save, post_delete, pre_save
from .models import InvoiceItem, InventoryLog

@receiver(pre_save, sender=InvoiceItem)
def capture_old_quantity(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_item = InvoiceItem.objects.get(pk=instance.pk)
            instance._old_quantity = old_item.quantity
        except InvoiceItem.DoesNotExist:
            instance._old_quantity = 0
    else:
        instance._old_quantity = 0

@receiver(post_save, sender=InvoiceItem)
def adjust_stock_on_save(sender, instance, created, **kwargs):
    change = 0
    reason = ""
    
    if created:
        change = -instance.quantity
        reason = f"Invoice #{instance.invoice.id} Created (Item Added)"
    else:
        old_qty = getattr(instance, '_old_quantity', 0)
        diff = instance.quantity - old_qty
        if diff != 0:
            change = -diff
            reason = f"Invoice #{instance.invoice.id} Item Updated"
            
    if change != 0:
        instance.product.stock += change
        instance.product.save()
        
        # Log it
        InventoryLog.objects.create(
            product=instance.product,
            product_name=instance.product.name,
            change=change,
            reason=reason
            # user field is tricky here as signals don't have request user. 
            # We skip user or use a middleware content if strictly needed.
        )

@receiver(post_delete, sender=InvoiceItem)
def return_stock_on_delete(sender, instance, **kwargs):
    from .models import Product
    from django.db import IntegrityError
    
    try:
        # Check if product exists in DB (handling case where product is deleted)
        if not Product.objects.filter(pk=instance.product_id).exists():
            return

        # Cache product name before potential deletion
        product_name = instance.product.name
        
        # Double check refresh
        instance.product.refresh_from_db()
        instance.product.stock += instance.quantity
        instance.product.save()
        
        InventoryLog.objects.create(
            product=instance.product,
            product_name=product_name,
            change=instance.quantity,
            reason=f"Invoice #{instance.invoice.id} Item Deleted"
        )
    except (Product.DoesNotExist, IntegrityError, Exception):
        # Product deleted or constraint failed - skip log
        pass

