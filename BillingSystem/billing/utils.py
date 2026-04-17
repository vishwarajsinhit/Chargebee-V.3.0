"""
Helper functions for currency formatting, role hierarchy, and report data consolidation.
"""


def get_user_role_level(user):
    """
    Get user's role level (2=Admin, 1=Client)
    """
    try:
        return user.role.role_level
    except:
        if user.is_superuser or user.is_staff:
            return 2
        return 1


def indian_currency_format(value, symbol="₹"):
    """
    Format a number as Indian currency (e.g. ₹X,XX,XXX.XX or Rs.X,XX,XXX.XX)
    """
    from decimal import Decimal
    
    try:
        # Convert to Decimal for precision
        if isinstance(value, str):
            value = Decimal(value)
        elif not isinstance(value, Decimal):
            value = Decimal(str(value))
        
        # Handle negative values
        is_negative = value < 0
        value = abs(value)
        
        # Split into integer and decimal parts
        str_value = f"{value:.2f}"
        parts = str_value.split('.')
        integer_part = parts[0]
        decimal_part = parts[1] if len(parts) > 1 else '00'
        
        # Format integer part with Indian number system
        if len(integer_part) <= 3:
            formatted = integer_part
        else:
            last_three = integer_part[-3:]
            other_digits = integer_part[:-3]
            
            formatted_other = ''
            for i, digit in enumerate(reversed(other_digits)):
                if i > 0 and i %2 == 0:
                    formatted_other = ',' + formatted_other
                formatted_other = digit + formatted_other
            
            formatted = formatted_other + ',' + last_three
        
        result = f"{symbol}{formatted}.{decimal_part}"
        if is_negative:
            result = '-' + result
            
        return result
        
    except (ValueError, TypeError, ArithmeticError):
        return f"{symbol}{value}"


def get_reports_context(symbol="₹"):
    """
    Centeralized function to generate context for business reports.
    Consolidates logic used by both web and PDF views.
    """
    from .models import Invoice, InvoiceItem, Company, Customer
    from django.db.models import Sum, Count
    from datetime import datetime
    
    company = Company.objects.first()
    outstanding_invoices_raw = Invoice.objects.filter(is_paid=False).order_by('-date')
    
    # Format currency for outstanding invoices
    # IMPORTANT: Calculate balance_due BEFORE formatting total_amount/amount_paid
    outstanding_invoices = []
    for invoice in outstanding_invoices_raw:
        # Calculate balance_due first while values are still numbers
        balance_due_value = invoice.balance_due
        
        # Create a dict with formatted values instead of modifying the object
        outstanding_invoices.append({
            'id': invoice.id,
            'customer': invoice.customer,
            'date': invoice.date,
            'total_amount': indian_currency_format(invoice.total_amount, symbol=symbol),
            'balance_due': indian_currency_format(balance_due_value, symbol=symbol)
        })
    
    # GST Summary (Collected only)
    # 1. GST from Invoice Items
    gst_from_items = InvoiceItem.objects.filter(invoice__is_paid=True).aggregate(Sum('gst_amount'))['gst_amount__sum'] or 0
    
    # 2. Fallback: GST from Invoices with NO items (Estimate 18% inclusive)
    # This handles legacy/imported data where items might be missing but total_amount exists
    invoices_without_items = Invoice.objects.filter(is_paid=True, items__isnull=True)
    gst_from_missing_items = 0
    
    for inv in invoices_without_items:
        # Assuming 18% GST inclusive: Amount = Base + (Base * 0.18) = Base * 1.18
        # GST = Amount - (Amount / 1.18)
        if inv.total_amount:
            gst_from_missing_items += float(inv.total_amount) - (float(inv.total_amount) / 1.18)
            
    total_gst = float(gst_from_items) + gst_from_missing_items
    total_gst_formatted = indian_currency_format(total_gst, symbol=symbol)
    
    # Top customers (By Revenue Realized)
    top_customers_raw = Invoice.objects.filter(is_paid=True).values('customer__name', 'customer__id').annotate(
        total_revenue=Sum('total_amount'),
        invoice_count=Count('id')
    ).order_by('-total_revenue')[:10]
    
    # Format currency in top_customers
    top_customers = []
    for customer in top_customers_raw:
        top_customers.append({
            'customer__name': customer['customer__name'],
            'total_revenue': indian_currency_format(customer['total_revenue'], symbol=symbol),
            'invoice_count': customer['invoice_count']
        })
    
    # Monthly sales
    current_year = datetime.now().year
    monthly_sales = []
    for month in range(1, 13):
        month_total = Invoice.objects.filter(
            date__year=current_year,
            date__month=month
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        monthly_sales.append({
            'month': month,
            'month_name': datetime(current_year, month, 1).strftime('%B'),
            'total': indian_currency_format(month_total, symbol=symbol)
        })
    
    return {
        'company': company,
        'outstanding_invoices': outstanding_invoices,
        'total_gst_collected': total_gst_formatted,
        'top_customers': top_customers,
        'monthly_sales': monthly_sales,
        'report_date': datetime.now()
    }
