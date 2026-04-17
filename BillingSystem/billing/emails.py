#To activate email 
#1. go in settings.py file 
#2. update the EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
"""
Email utilities for the Billing system.
Handles rendering and sending invoice emails with PDF attachments.
Handles rendering and sending invoice emails with PDF attachments.
"""

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


def send_invoice_email(invoice, recipient_email=None, request=None):
    """
    Send an invoice via email with PDF attachment.
    
    Args:
        invoice: Invoice instance
        recipient_email: Email address to send to (defaults to invoice.customer.email)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Use provided email or fall back to customer email
        to_email = recipient_email or invoice.customer.email
        
        if not to_email:
            return False, "No email address provided"
        
        # Get company details
        from .models import Company
        company = Company.objects.first()
        
        # Generate PDF
        from .views import generate_invoice_pdf_bytes
        pdf_bytes = generate_invoice_pdf_bytes(invoice)
        
        # Prepare email context
        context = {
            'invoice': invoice,
            'customer': invoice.customer,
            'company': company,
            'items': invoice.items.all(),
            'request': request,
        }
        
        # Render email HTML
        html_message = render_to_string('admin_panel/invoice_email.html', context)
        
        # Create email subject
        subject = f"Invoice #{invoice.id} from {company.name if company else 'Chargebee'}"
        
        # Create email message
        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        email.content_subtype = 'html'
        
        # Attach PDF
        pdf_filename = f"Invoice_{invoice.id}.pdf"
        email.attach(pdf_filename, pdf_bytes, 'application/pdf')
        
        # Send email
        email.send(fail_silently=False)
        
        # Update invoice email tracking
        invoice.emailed_at = timezone.now()
        invoice.emailed_to = to_email
        invoice.save(update_fields=['emailed_at', 'emailed_to'])
        
        logger.info(f"Invoice #{invoice.id} emailed successfully to {to_email}")
        return True, f"Invoice emailed successfully to {to_email}"
        
    except Exception as e:
        error_msg = f"Failed to email invoice: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
