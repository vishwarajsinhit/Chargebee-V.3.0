#To activate razorpay payment gateway 
#1. go in settings.py file 
#2. update the RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET 

"""
Razorpay payment integration views.
Handles order creation, signature verification, and secure transaction recording.
Ref: https://razorpay.com/docs/api/
"""
import razorpay
import logging
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Invoice, Transaction, ActivityLog, RazorpayPayment
from .permissions import filter_invoices_by_role
from .utils import indian_currency_format

logger = logging.getLogger(__name__)

@login_required
def initiate_razorpay_payment(request, pk):
    """
    Create a Razorpay order for an invoice.
    Ref: https://razorpay.com/docs/api/orders/#create-an-order
    """
    try:
        invoice = get_object_or_404(Invoice, pk=pk)
        
        # Verify user has permission to view this invoice
        allowed_invoices = filter_invoices_by_role(request.user, Invoice.objects.all())
        if invoice not in allowed_invoices:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Calculate amount to be paid (default to balance_due, or use requested amount)
        requested_amount = request.GET.get('amount')
        if requested_amount:
            try:
                amount_in_rupees = float(requested_amount)
                # Clamp to balance_due
                if amount_in_rupees > invoice.balance_due:
                    amount_in_rupees = invoice.balance_due
            except ValueError:
                amount_in_rupees = invoice.balance_due
        else:
            amount_in_rupees = invoice.balance_due
            
        amount_in_paise = int(amount_in_rupees * 100)
        
        # Razorpay default transaction limit is ₹5,00,000 (50,000,000 paise)
        MAX_RAZORPAY_AMOUNT_PAISE = 5000000000 
        if amount_in_paise > MAX_RAZORPAY_AMOUNT_PAISE:
            logger.warning(f"Invoice {invoice.id} amount {amount_in_paise} paise exceeds Razorpay limit. Capping to {MAX_RAZORPAY_AMOUNT_PAISE} paise.")
            amount_in_paise = MAX_RAZORPAY_AMOUNT_PAISE
            amount_in_rupees = amount_in_paise / 100
        
        if amount_in_paise <= 0:
            return JsonResponse({'error': 'Invoice is already fully paid'}, status=400)
        
        # Log configuration
        logger.info(f"Initializing Razorpay payment for invoice {invoice.id}")
        logger.info(f"Amount: ₹{amount_in_rupees} ({amount_in_paise} paise)")
        
        # Initialize Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Create Razorpay order
        order_data = {
            'amount': amount_in_paise,
            'currency': 'INR',
            'receipt': f'invoice_{invoice.id}',
            'notes': {
                'invoice_id': invoice.id,
                'customer_name': invoice.customer.name,
                'customer_email': invoice.customer.email,
            }
        }
        
        razorpay_order = client.order.create(data=order_data)
        logger.info(f"Razorpay order created: {razorpay_order.get('id')}")
        
        # Save RazorpayPayment record
        RazorpayPayment.objects.create(
            invoice=invoice,
            razorpay_order_id=razorpay_order['id'],
            amount=amount_in_paise,
            currency='INR',
            status='CREATED'
        )
        
        # Return order details for frontend
        return JsonResponse({
            'order_id': razorpay_order['id'],
            'amount': amount_in_paise,
            'currency': 'INR',
            'key_id': settings.RAZORPAY_KEY_ID,
            'name': invoice.customer.name,
            'email': invoice.customer.email,
            'invoice_id': invoice.id,
        })
        
    except razorpay.errors.BadRequestError as e:
        logger.error(f"Razorpay BadRequestError: {str(e)}")
        return JsonResponse({'error': f'Invalid request to Razorpay: {str(e)}'}, status=400)
    except razorpay.errors.GatewayError as e:
        logger.error(f"Razorpay GatewayError: {str(e)}")
        return JsonResponse({'error': 'Razorpay service temporarily unavailable.'}, status=502)
    except Exception as e:
        logger.error(f"Unexpected error in initiate_razorpay_payment: {type(e).__name__}: {str(e)}")
        return JsonResponse({'error': f'Unexpected error: {str(e)}'}, status=500)


@login_required
def verify_razorpay_payment(request, pk):
    """
    Verify and record successful Razorpay payment.
    Ref: https://razorpay.com/docs/api/payments/#verify-signature-for-web-sdk
    """
    if request.method == 'POST':
        try:
            invoice = get_object_or_404(Invoice, pk=pk)
            
            # Get payment details from POST
            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_signature = request.POST.get('razorpay_signature')
            
            # Find the RazorpayPayment record
            payment = get_object_or_404(RazorpayPayment, razorpay_order_id=razorpay_order_id)
            
            # Update payment details
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            
            # Verify signature
            if payment.verify_signature(razorpay_signature):
                payment.status = 'SUCCESS'
                payment.save()
                
                # Create Transaction record
                amount_in_rupees = payment.amount / 100
                Transaction.objects.create(
                    invoice=invoice,
                    amount=amount_in_rupees,
                    payment_method='ONLINE'
                )
                
                # Update invoice payment status
                invoice.update_payment_status()
                
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='CREATE',
                    model_name='Transaction',
                    object_id=invoice.id,
                    object_repr=f'Invoice #{invoice.id}',
                    details=f'Razorpay payment of ₹{amount_in_rupees} for Invoice #{invoice.id}'
                )
                
                messages.success(request, f'Payment of ₹{amount_in_rupees:.2f} received successfully via Razorpay!')
            else:
                payment.status = 'FAILED'
                payment.save()
                messages.error(request, 'Payment verification failed. Please contact support.')
                
        except Exception as e:
            messages.error(request, f'Error processing payment: {str(e)}')
    
    return redirect('invoice_detail', pk=pk)
