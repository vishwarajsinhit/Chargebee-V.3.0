"""
Web UI and API views for the Billing application.
Includes Dashboard, CRUD operations for Customers, Products, and Invoices,
as well as PDF generation and background email tasks.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, DetailView, UpdateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from calendar import month_abbr
import json

from django.contrib.auth.models import User
from dateutil.relativedelta import relativedelta
from .models import Customer, Product, Invoice, InvoiceItem, Transaction, Company, CustomerAssignment, UserRole, UserProfile, ActivityLog, RazorpayPayment, InventoryLog
from .utils import get_user_role_level, get_reports_context, indian_currency_format
from .permissions import filter_invoices_by_role
from .payments import initiate_razorpay_payment, verify_razorpay_payment # Razorpay API: https://razorpay.com/docs/api/

# --- Web UI Views ---
 
class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Main dashboard for both Admins and Clients.
    Calculates financial metrics, recent activity, and chart data based on user roles.
    """
    template_name = 'general/dashboard.html'

    def get_context_data(self, **kwargs):
        
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Base Querysets filtered by role
        invoices = filter_invoices_by_role(user, Invoice.objects.all())
        
        # Financials (Calculated first to be used below)
        total_revenue = invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        context['total_revenue'] = indian_currency_format(total_revenue)
        
        # Profit & Loss
        from .models import Expense
        total_expenses = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        net_profit = total_revenue - total_expenses
        context['total_expenses'] = indian_currency_format(total_expenses)
        context['net_profit'] = indian_currency_format(net_profit)
        context['is_profit'] = net_profit >= 0
        
        # Stats based on filtered invoices
        context['total_invoices'] = invoices.count()
        context['pending_invoices'] = invoices.filter(is_paid=False).count()
        context['pending_reminders'] = invoices.filter(is_paid=False, reminder_sent=True).count()
        context['paid_invoices'] = invoices.filter(is_paid=True).count()
        
        if hasattr(user, 'role') and user.role.role == 'client':
            context['total_customers'] = 1 # Client views themselves
            context['is_client'] = True
            
            # Client specific metrics (Fix: Use Transaction aggregation instead of property)
            paid_amount = Transaction.objects.filter(invoice__in=invoices).aggregate(Sum('amount'))['amount__sum'] or 0
            context['paid_amount'] = indian_currency_format(paid_amount)
            unpaid_amount = invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            unpaid_amount = unpaid_amount - paid_amount
            context['unpaid_amount'] = indian_currency_format(unpaid_amount)
            
            if context['total_invoices'] > 0:
                context['paid_percentage'] = round((context['paid_invoices'] / context['total_invoices']) * 100, 1)
                context['unpaid_percentage'] = round((context['pending_invoices'] / context['total_invoices']) * 100, 1)
            else:
                context['paid_percentage'] = 0
                context['unpaid_percentage'] = 0
                
        else:
            context['total_customers'] = Customer.objects.count()
            context['is_client'] = False
            context['total_users'] = User.objects.count()
            context['total_products'] = Product.objects.count()
            # Active customers (last 7 days)
            seven_days_ago = timezone.now() - timedelta(days=7)
            context['active_customers'] = Customer.objects.filter(
                invoice__date__gte=seven_days_ago
            ).distinct().count()
            # Collection rate
            total = invoices.count()
            paid = invoices.filter(is_paid=True).count()
            context['collection_rate'] = (paid / total * 100) if total > 0 else 0
        
        # Average Invoice Value
        avg_invoice_value = invoices.aggregate(Avg('total_amount'))['total_amount__avg'] or 0
        context['avg_invoice_value'] = indian_currency_format(avg_invoice_value)
        
        # Outstanding
        unpaid_invoices = invoices.filter(is_paid=False)
        outstanding_amount = sum(inv.balance_due for inv in unpaid_invoices)
        context['outstanding_amount'] = indian_currency_format(outstanding_amount)
        
        # Monthly Stat
        current_month = datetime.now().month
        current_year = datetime.now().year
        monthly_revenue = invoices.filter(
            date__month=current_month,
            date__year=current_year
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        context['monthly_revenue'] = indian_currency_format(monthly_revenue)
        
        # Recent Activity
        recent_invoices = list(invoices.order_by('-date')[:5])
        for invoice in recent_invoices:
            invoice.total_amount = indian_currency_format(invoice.total_amount)
        context['recent_invoices'] = recent_invoices
        
        # Chart Data
        today = datetime.now()
        months_labels = []
        months_data = []
        
        for i in range(5, -1, -1):
            target_date = today - timedelta(days=30*i)
            month_rev = invoices.filter(
                date__month=target_date.month,
                date__year=target_date.year
            ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            
            months_labels.append(month_abbr[target_date.month])
            months_data.append(float(month_rev))
        
        context['revenue_chart_labels'] = json.dumps(months_labels)
        context['revenue_chart_data'] = json.dumps(months_data)
        
        context['paid_count'] = context['paid_invoices']
        context['unpaid_count'] = context['pending_invoices']

        # For demo purposes, we can hardcode something or calculate if we had a target
        context['revenue_growth'] = {
            'value': 12.5,
            'is_positive': True
        }
        
        return context

    def get_template_names(self):
        if hasattr(self.request.user, 'role') and self.request.user.role.role == 'client':
            return ['general/dashboard.html']
        return [self.template_name]


from .forms import ClientUserForm, ClientProfileForm

class ClientProfileView(LoginRequiredMixin, TemplateView):
    """View for clients to manage their personal and company profile."""
    template_name = 'client_panel/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Ensure the user has a profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Backfill legacy customer data to profile if profile is empty
        if not profile.company_name and not profile.phone:
            assignment = CustomerAssignment.objects.filter(user=user).first()
            if assignment and assignment.customer:
                cust = assignment.customer
                profile.company_name = cust.company_name
                profile.contact_person = cust.contact_person
                profile.company_type = cust.company_type
                profile.address1 = cust.address1
                profile.address2 = cust.address2
                profile.landmark = cust.landmark
                profile.city = cust.city
                profile.state = cust.state
                profile.pincode = cust.pincode
                profile.country = cust.country
                profile.phone = cust.phone
                profile.save()
        
        if self.request.method == 'POST':
            # POST handled in post() but we need forms in context 
            # if we wanted to re-render with errors
            pass
        else:
            context['user_form'] = ClientUserForm(instance=user)
            context['profile_form'] = ClientProfileForm(instance=profile)
            
        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        user_form = ClientUserForm(request.POST, instance=user)
        profile_form = ClientProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            
            # Synchronize profile updates to associated Customer records
            assigned_customers = Customer.objects.filter(assignments__user=user)
            for customer in assigned_customers:
                customer.company_name = profile.company_name
                customer.contact_person = profile.contact_person or f"{user.first_name} {user.last_name}".strip()
                customer.company_type = profile.company_type
                customer.address1 = profile.address1
                customer.address2 = profile.address2
                customer.landmark = profile.landmark
                customer.city = profile.city
                customer.state = profile.state
                customer.pincode = profile.pincode
                customer.country = profile.country
                customer.phone = profile.phone
                customer.email = user.email
                
                # Update legacy address field for backwards compatibility
                address_parts = [p for p in [profile.address1, profile.address2, profile.landmark] if p]
                loc_parts = [p for p in [profile.city, profile.state, profile.pincode] if p]
                if loc_parts:
                    address_parts.append(", ".join(loc_parts))
                if profile.country and profile.country != 'India':
                    address_parts.append(profile.country)
                customer.address = "\n".join(address_parts)
                
                customer.save()
                
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('client_profile')
            
        context = self.get_context_data(**kwargs)
        context['user_form'] = user_form
        context['profile_form'] = profile_form
        messages.error(request, "Please correct the errors below.")
        return self.render_to_response(context)

def about_view(request):
    """View for displaying application information and credits."""
    return render(request, 'general/about.html')

class InvoiceListView(LoginRequiredMixin, ListView):
    """View to list and search invoices, filtered by user permission."""
    model = Invoice
    template_name = 'client_panel/invoice_management.html'
    context_object_name = 'invoices'
    def get_queryset(self):
        from .permissions import filter_invoices_by_role
        queryset = filter_invoices_by_role(self.request.user, Invoice.objects.all())
        
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(id__icontains=query) |
                Q(customer__name__icontains=query) |
                Q(customer__email__icontains=query)
            )
        return queryset.order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view_mode'] = 'list'
        context['search_query'] = self.request.GET.get('q', '')
        
        # Format currency for each invoice
        for invoice in context['invoices']:
            invoice.total_amount = indian_currency_format(invoice.total_amount)
        
        return context

class InvoiceDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a single invoice, with items, transactions, and feedback."""
    model = Invoice
    template_name = 'client_panel/invoice_management.html'
    context_object_name = 'invoice'

    def get_queryset(self):
        from .permissions import filter_invoices_by_role
        return filter_invoices_by_role(self.request.user, Invoice.objects.all())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view_mode'] = 'detail'
        try:
            context['company'] = Company.objects.first()
        except:
            context['company'] = {'name': 'Your Company', 'address': '', 'email': ''}
        
        # Get balance_due while it's still a number (for calculations if needed)
        invoice = self.object
        balance_due_value = invoice.balance_due
        
        # Pre-format currency values for template display
        items = list(invoice.items.all())
        for item in items:
            item.formatted_price = indian_currency_format(item.price)
            item.formatted_subtotal = indian_currency_format(item.subtotal)
            item.formatted_gst_amount = indian_currency_format(item.gst_amount)
            item.formatted_total_with_tax = indian_currency_format(item.total_with_tax)
        context['formatted_items'] = items
        context['formatted_total_amount'] = indian_currency_format(invoice.total_amount)
        context['formatted_amount_paid'] = indian_currency_format(invoice.amount_paid)
        context['formatted_balance_due'] = indian_currency_format(invoice.balance_due)
        
        context['transactions'] = self.object.transactions.all()
        context['feedbacks'] = self.object.feedbacks.select_related('user').all()
        return context

class InvoiceCreateView(LoginRequiredMixin, CreateView):
    """Admin-only view to create new invoices."""
    model = Invoice
    template_name = 'client_panel/invoice_management.html'
    fields = []
    
    def dispatch(self, request, *args, **kwargs):
        if hasattr(request.user, 'role') and request.user.role.role == 'client':
            return redirect('invoice_list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view_mode'] = 'form'
        context['customers'] = Customer.objects.all()
        context['products'] = Product.objects.all()
        return context

class InvoiceUpdateView(LoginRequiredMixin, UpdateView):
    """Admin-only view to edit existing invoices, using the React/JS frontend payload."""
    model = Invoice
    template_name = 'client_panel/invoice_management.html'
    fields = []
    
    def dispatch(self, request, *args, **kwargs):
        # Prevent clients from editing invoices
        if hasattr(request.user, 'role') and request.user.role.role == 'client':
            return redirect('invoice_list')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        from .serializers import InvoiceSerializer
        import json
        
        context = super().get_context_data(**kwargs)
        context['view_mode'] = 'form' # Re-use the form view
        context['customers'] = Customer.objects.all()
        context['products'] = Product.objects.all()
        context['edit_mode'] = True
        
        # Serialize existing invoice data for JS to populate
        serializer = InvoiceSerializer(self.object)
        context['invoice_json'] = json.dumps(serializer.data, default=str)
        
        return context

@login_required
def invoice_delete(request, pk):
    # Idempotent delete: if it exists, delete it; if not, just redirect.
    # This prevents 404s on double-clicks or browser pre-fetching.
    Invoice.objects.filter(pk=pk).delete()
    return redirect('invoice_list')

from django.http import JsonResponse
from django.views.decorators.http import require_POST

@login_required
@require_POST
def quick_customer_add(request):
    """AJAX endpoint to quickly create a customer from the Create Invoice page."""
    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()

    if not name or not email:
        return JsonResponse({'success': False, 'error': 'Name and email are required.'}, status=400)

    # If customer with email already exists, return it
    existing = Customer.objects.filter(email=email).first()
    if existing:
        return JsonResponse({
            'success': True,
            'customer': {'id': existing.id, 'name': existing.name, 'email': existing.email},
            'message': f'Existing customer "{existing.name}" selected.'
        })

    try:
        customer = Customer.objects.create(name=name, email=email)
        
        # If the user creating the customer has a profile, populate the customer details
        if hasattr(request.user, 'profile'):
            profile = request.user.profile
            customer.company_name = profile.company_name
            customer.contact_person = profile.contact_person or f"{request.user.first_name} {request.user.last_name}".strip()
            customer.company_type = profile.company_type
            customer.phone = profile.phone
            customer.address1 = profile.address1
            customer.address2 = profile.address2
            customer.landmark = profile.landmark
            customer.city = profile.city
            customer.state = profile.state
            customer.pincode = profile.pincode
            customer.country = profile.country
            
            # Legacy field for compatibility
            address_parts = [p for p in [profile.address1, profile.address2, profile.landmark] if p]
            loc_parts = [p for p in [profile.city, profile.state, profile.pincode] if p]
            if loc_parts:
                address_parts.append(", ".join(loc_parts))
            if profile.country and profile.country != 'India':
                address_parts.append(profile.country)
            
            customer.address = "\n".join(address_parts)
            customer.save()
            
            # Auto-assign this customer to the user
            CustomerAssignment.objects.get_or_create(
                user=request.user,
                customer=customer,
                defaults={'assigned_by': request.user}
            )
            
        return JsonResponse({
            'success': True,
            'customer': {'id': customer.id, 'name': customer.name, 'email': customer.email},
            'message': f'Customer "{customer.name}" created!'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def generate_pdf(request, pk):
    """Utility view to generate a PDF for an invoice and serve it as a download."""
    import base64
    from django.conf import settings
    
    invoice = get_object_or_404(Invoice, pk=pk)
    company = Company.objects.first()
    
    # Get balance_due while it's still a number
    balance_due_value = invoice.balance_due
    
    # Get items for the template
    items = list(invoice.items.all())
    
    # Convert images to base64 data URIs for PDF generation
    qr_code_base64 = None
    company_logo_base64 = None
    
    if invoice.qr_code:
        qr_code_file_path = settings.MEDIA_ROOT / invoice.qr_code.name
        if qr_code_file_path.exists():
            with open(qr_code_file_path, 'rb') as f:
                qr_code_data = base64.b64encode(f.read()).decode()
                qr_code_base64 = f'data:image/png;base64,{qr_code_data}'
    
    if company and company.logo:
        company_logo_file_path = settings.MEDIA_ROOT / company.logo.name
        if company_logo_file_path.exists():
            with open(company_logo_file_path, 'rb') as f:
                get_image_format = company_logo_file_path.suffix.lower().replace('.', '')
                if get_image_format == 'jpg':
                    get_image_format = 'jpeg'
                logo_data = base64.b64encode(f.read()).decode()
                company_logo_base64 = f'data:image/{get_image_format};base64,{logo_data}'
    
    # Pre-format currency values for PDF template
    for item in items:
        item.formatted_price = indian_currency_format(item.price, symbol="Rs.")
        item.formatted_subtotal = indian_currency_format(item.subtotal, symbol="Rs.")
        item.formatted_gst_amount = indian_currency_format(item.gst_amount, symbol="Rs.")
        item.formatted_total_with_tax = indian_currency_format(item.total_with_tax, symbol="Rs.")
    
    context = {
        'invoice': invoice,
        'company': company,
        'items': items,
        'qr_code_base64': qr_code_base64,
        'company_logo_base64': company_logo_base64,
        'formatted_total_amount': indian_currency_format(invoice.total_amount, symbol="Rs."),
        'formatted_amount_paid': indian_currency_format(invoice.amount_paid, symbol="Rs."),
        'formatted_balance_due': indian_currency_format(invoice.balance_due, symbol="Rs."),
    }
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{pk}.pdf"'
    
    template_path = 'client_panel/invoice_pdf_template.html'
    template = get_template(template_path)
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

def generate_invoice_pdf_bytes(invoice):
    """
    Generate invoice PDF and return as bytes (for email attachment).
    """
    import base64
    from django.conf import settings
    from io import BytesIO
    
    company = Company.objects.first()
    items = list(invoice.items.all())
    
    # Convert images to base64 data URIs for PDF generation
    qr_code_base64 = None
    company_logo_base64 = None
    
    if invoice.qr_code:
        qr_code_file_path = settings.MEDIA_ROOT / invoice.qr_code.name
        if qr_code_file_path.exists():
            with open(qr_code_file_path, 'rb') as f:
                qr_code_data = base64.b64encode(f.read()).decode()
                qr_code_base64 = f'data:image/png;base64,{qr_code_data}'
    
    if company and company.logo:
        company_logo_file_path = settings.MEDIA_ROOT / company.logo.name
        if company_logo_file_path.exists():
            with open(company_logo_file_path, 'rb') as f:
                get_image_format = company_logo_file_path.suffix.lower().replace('.', '')
                if get_image_format == 'jpg':
                    get_image_format = 'jpeg'
                logo_data = base64.b64encode(f.read()).decode()
                company_logo_base64 = f'data:image/{get_image_format};base64,{logo_data}'
    
    # Pre-format currency values for PDF template
    for item in items:
        item.formatted_price = indian_currency_format(item.price, symbol="Rs.")
        item.formatted_subtotal = indian_currency_format(item.subtotal, symbol="Rs.")
        item.formatted_gst_amount = indian_currency_format(item.gst_amount, symbol="Rs.")
        item.formatted_total_with_tax = indian_currency_format(item.total_with_tax, symbol="Rs.")
    
    context = {
        'invoice': invoice,
        'company': company,
        'items': items,
        'qr_code_base64': qr_code_base64,
        'company_logo_base64': company_logo_base64,
        'formatted_total_amount': indian_currency_format(invoice.total_amount, symbol="Rs."),
        'formatted_amount_paid': indian_currency_format(invoice.amount_paid, symbol="Rs."),
        'formatted_balance_due': indian_currency_format(invoice.balance_due, symbol="Rs."),
        'tax_amount': invoice.total_amount - sum(item.price * item.quantity for item in invoice.items.all()),
    }
    
    template_path = 'client_panel/invoice_pdf_template.html'
    template = get_template(template_path)
    html = template.render(context)
    
    # Generate PDF to BytesIO buffer
    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_buffer)
    
    if pisa_status.err:
        raise Exception("Error generating PDF")
    
    # Get PDF bytes
    pdf_bytes = pdf_buffer.getvalue()
    pdf_buffer.close()
    
    return pdf_bytes

@login_required
def email_invoice(request, pk):
    """Send invoice via email"""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    # Import email utility
    from .emails import send_invoice_email
    import threading
    
    # Get recipient email (allow override via POST or use customer email)
    if request.method == 'POST':
        recipient_email = request.POST.get('recipient_email', invoice.customer.email)
    else:
        recipient_email = invoice.customer.email
    
    # Define a target function for the thread
    def send_email_task(inv_id, recipient, req):
        try:
            # Re-fetch invoice inside thread to avoid passing Django model instances between threads
            inv = Invoice.objects.get(pk=inv_id)
            send_invoice_email(inv, recipient, request=req)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Background email failed: {str(e)}")
            
    # Start the background thread
    email_thread = threading.Thread(target=send_email_task, args=(invoice.id, recipient_email, request))
    email_thread.daemon = True
    email_thread.start()
    
    # Add immediate message to display to user
    from django.contrib import messages
    messages.success(request, f"Invoice email is being generated and sent to {recipient_email} in the background. It should arrive shortly!")
    
    return redirect('invoice_detail', pk=pk)

@login_required
def record_payment(request, pk):
    if request.method == 'POST':
        invoice = get_object_or_404(Invoice, pk=pk)
        amount = request.POST.get('amount')
        method = request.POST.get('method', 'CASH')  # Default to CASH if not provided
        
        # No longer enforcing balance_due for clients to allow partial payments
        if amount and float(amount) > 0:
            Transaction.objects.create(
                invoice=invoice,
                amount=amount,
                payment_method=method
            )
            invoice.update_payment_status()
            
    return redirect('invoice_detail', pk=pk)

@login_required
def submit_invoice_feedback(request, pk):
    if request.method == 'POST':
        invoice = get_object_or_404(Invoice, pk=pk)
        message = request.POST.get('message', '').strip()
        
        # Security: Allow only if user is admin OR the invoice belongs to them
        can_feedback = False
        if hasattr(request.user, 'role') and request.user.role.role == 'client':
            # Check if this invoice is for a customer assigned to this client
            customer_ids = request.user.customer_assignments.values_list('customer_id', flat=True)
            if invoice.customer_id in customer_ids:
                can_feedback = True
        else:
            # Admins can comment on any invoice
            can_feedback = True
            
        if message and can_feedback:
            from .models import InvoiceFeedback
            InvoiceFeedback.objects.create(
                invoice=invoice,
                user=request.user,
                message=message
            )
            
    return redirect('invoice_detail', pk=pk)

@login_required
def generate_reports_pdf(request):
    context = get_reports_context(symbol="Rs.")
    context['view_mode'] = 'pdf'
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="business_report_{context["report_date"].strftime("%Y%m%d")}.pdf"'
    
    template = get_template('admin_panel/reports_overview.html')
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Error generating PDF')
    return response

# --- Management Views ---

class CustomerListView(LoginRequiredMixin, ListView):
    """View to list and search customers, including their assigned users."""
    model = Customer
    template_name = 'admin_panel/customer_management.html'
    context_object_name = 'customers'
    ordering = ['name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(email__icontains=query) |
                Q(phone__icontains=query)
            )
        # Prefetch assigned users to display credentials in the list
        return queryset.prefetch_related('assignments__user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context

from .forms import CustomerForm, ProductForm

class CustomerCreateView(LoginRequiredMixin, CreateView):
    """Admin view to create new customers and associate them with existing client users."""
    model = Customer
    template_name = 'admin_panel/customer_management.html'
    form_class = CustomerForm
    success_url = '/customers/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass user data for auto-filling form
        users = User.objects.filter(role__role='client')
        user_map = {}
        for u in users:
            # Construct full address from all address fields
            address_parts = []
            if hasattr(u, 'profile'):
                if u.profile.address1:
                    address_parts.append(u.profile.address1)
                if u.profile.address2:
                    address_parts.append(u.profile.address2)
                if u.profile.landmark:
                    address_parts.append(u.profile.landmark)
                
                # Add city, state, pincode on separate line
                location_parts = []
                if u.profile.city:
                    location_parts.append(u.profile.city)
                if u.profile.state:
                    location_parts.append(u.profile.state)
                if u.profile.pincode:
                    location_parts.append(u.profile.pincode)
                if location_parts:
                    address_parts.append(', '.join(location_parts))
                
                if u.profile.country and u.profile.country != 'India':
                    address_parts.append(u.profile.country)
                
                full_address = '\n'.join(address_parts) if address_parts else u.profile.address
            else:
                full_address = ''
            
            # Get profile phone and address
            profile_phone = getattr(u.profile, 'phone', '') if hasattr(u, 'profile') else ''
            
            # Also check if there's an existing Customer with the same email for better phone/address fallback
            existing_customer = Customer.objects.filter(email=u.email).first()
            phone_value = profile_phone or (existing_customer.phone if existing_customer else '')
            address_value = full_address or (existing_customer.address if existing_customer else '')
            
            user_map[u.id] = {
                'name': f"{u.first_name} {u.last_name}".strip() or u.username,
                'email': u.email,
                'phone': phone_value,
                'address': address_value,
                'company_name': getattr(u.profile, 'company_name', '') if hasattr(u, 'profile') else '',
                'contact_person': getattr(u.profile, 'contact_person', '') if hasattr(u, 'profile') else '',
                'company_type': getattr(u.profile, 'company_type', '') if hasattr(u, 'profile') else '',
                'address1': getattr(u.profile, 'address1', '') if hasattr(u, 'profile') else '',
                'address2': getattr(u.profile, 'address2', '') if hasattr(u, 'profile') else '',
                'landmark': getattr(u.profile, 'landmark', '') if hasattr(u, 'profile') else '',
                'pincode': getattr(u.profile, 'pincode', '') if hasattr(u, 'profile') else '',
                'city': getattr(u.profile, 'city', '') if hasattr(u, 'profile') else '',
                'state': getattr(u.profile, 'state', '') if hasattr(u, 'profile') else '',
                'country': getattr(u.profile, 'country', 'India') if hasattr(u, 'profile') else 'India',
            }
        context['user_data_json'] = json.dumps(user_map)
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        assigned_user = form.cleaned_data.get('assigned_user')
        
        # If not manually selected, try to auto-match by email
        if not assigned_user:
            from django.contrib.auth.models import User
            assigned_user = User.objects.filter(email=self.object.email).first()
            
        if assigned_user:
            # For creation, just create. For update, clear first (handled below or just recreate)
            CustomerAssignment.objects.get_or_create(
                user=assigned_user,
                customer=self.object,
                defaults={'assigned_by': self.request.user}
            )
            
            # Synchronize customer data back to UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=assigned_user)
            profile.company_name = self.object.company_name
            profile.contact_person = self.object.contact_person
            profile.company_type = self.object.company_type
            profile.address1 = self.object.address1
            profile.address2 = self.object.address2
            profile.landmark = self.object.landmark
            profile.city = self.object.city
            profile.state = self.object.state
            profile.pincode = self.object.pincode
            profile.country = self.object.country
            profile.phone = self.object.phone
            profile.save()
            
            # Sync email back to User
            if assigned_user.email != self.object.email:
                assigned_user.email = self.object.email
                assigned_user.save()
            
        return response

class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    """Admin view to edit customer details and update their user assignments."""
    model = Customer
    template_name = 'admin_panel/customer_management.html'
    form_class = CustomerForm
    success_url = '/customers/'
    
    def get_initial(self):
        initial = super().get_initial()
        # Pre-populate existing assignment
        assignment = self.object.assignments.first()
        if assignment:
            initial['assigned_user'] = assignment.user
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = User.objects.filter(role__role='client')
        user_map = {}
        for u in users:
            # Construct full address from all address fields
            address_parts = []
            if hasattr(u, 'profile'):
                if u.profile.address1:
                    address_parts.append(u.profile.address1)
                if u.profile.address2:
                    address_parts.append(u.profile.address2)
                if u.profile.landmark:
                    address_parts.append(u.profile.landmark)
                
                # Add city, state, pincode on separate line
                location_parts = []
                if u.profile.city:
                    location_parts.append(u.profile.city)
                if u.profile.state:
                    location_parts.append(u.profile.state)
                if u.profile.pincode:
                    location_parts.append(u.profile.pincode)
                if location_parts:
                    address_parts.append(', '.join(location_parts))
                
                if u.profile.country and u.profile.country != 'India':
                    address_parts.append(u.profile.country)
                
                full_address = '\n'.join(address_parts) if address_parts else u.profile.address
            else:
                full_address = ''
            
            # Get profile phone and address
            profile_phone = getattr(u.profile, 'phone', '') if hasattr(u, 'profile') else ''
            
            # Also check if there's an existing Customer with the same email for better phone/address fallback
            existing_customer = Customer.objects.filter(email=u.email).first()
            phone_value = profile_phone or (existing_customer.phone if existing_customer else '')
            address_value = full_address or (existing_customer.address if existing_customer else '')
            
            user_map[u.id] = {
                'name': f"{u.first_name} {u.last_name}".strip() or u.username,
                'email': u.email,
                'phone': phone_value,
                'address': address_value,
                'company_name': getattr(u.profile, 'company_name', '') if hasattr(u, 'profile') else '',
                'contact_person': getattr(u.profile, 'contact_person', '') if hasattr(u, 'profile') else '',
                'company_type': getattr(u.profile, 'company_type', '') if hasattr(u, 'profile') else '',
                'address1': getattr(u.profile, 'address1', '') if hasattr(u, 'profile') else '',
                'address2': getattr(u.profile, 'address2', '') if hasattr(u, 'profile') else '',
                'landmark': getattr(u.profile, 'landmark', '') if hasattr(u, 'profile') else '',
                'pincode': getattr(u.profile, 'pincode', '') if hasattr(u, 'profile') else '',
                'city': getattr(u.profile, 'city', '') if hasattr(u, 'profile') else '',
                'state': getattr(u.profile, 'state', '') if hasattr(u, 'profile') else '',
                'country': getattr(u.profile, 'country', 'India') if hasattr(u, 'profile') else 'India',
            }
        context['user_data_json'] = json.dumps(user_map)
        return context
        
    def form_valid(self, form):
        response = super().form_valid(form)
        assigned_user = form.cleaned_data.get('assigned_user')
        
        # If not manually selected, try to auto-match by email
        if not assigned_user:
            from django.contrib.auth.models import User
            assigned_user = User.objects.filter(email=self.object.email).first()
            
        # Clear existing assignments (only if we have a new one or specifically want to clear)
        CustomerAssignment.objects.filter(customer=self.object).delete()
        
        if assigned_user:
            CustomerAssignment.objects.create(
                user=assigned_user,
                customer=self.object,
                assigned_by=self.request.user
            )
            
            # Synchronize customer data back to UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=assigned_user)
            profile.company_name = self.object.company_name
            profile.contact_person = self.object.contact_person
            profile.company_type = self.object.company_type
            profile.address1 = self.object.address1
            profile.address2 = self.object.address2
            profile.landmark = self.object.landmark
            profile.city = self.object.city
            profile.state = self.object.state
            profile.pincode = self.object.pincode
            profile.country = self.object.country
            profile.phone = self.object.phone
            profile.save()
            
            # Sync email back to User
            if assigned_user.email != self.object.email:
                assigned_user.email = self.object.email
                assigned_user.save()
            
        return response

@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    customer.delete()
    return redirect('customer_list')

# --- Product Management Views ---

class ProductListView(LoginRequiredMixin, ListView):
    """Publicly viewable product catalog, filtered by search and category."""
    model = Product
    template_name = 'client_panel/product_catalog.html'
    context_object_name = 'products'
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(hsn_code__icontains=query)
            )
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['categories'] = ProductCategory.objects.all()
        context['selected_category'] = self.request.GET.get('category', '')
        
        # Format currency for each product
        for product in context['products']:
            product.price = indian_currency_format(product.price)
        
        return context

class ProductCreateView(LoginRequiredMixin, CreateView):
    """Admin-only view to add products and initialize their stock levels."""
    model = Product
    template_name = 'client_panel/product_catalog.html'
    form_class = ProductForm
    success_url = '/products/'

    def dispatch(self, request, *args, **kwargs):
        if hasattr(request.user, 'role') and request.user.role.role == 'client':
            return redirect('product_list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Log initial stock if product has stock
        if self.object.stock > 0:
            InventoryLog.objects.create(
                product=self.object,
                change=self.object.stock,
                reason='Initial stock - Product created',
                user=self.request.user
            )
        return response

class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    template_name = 'client_panel/product_catalog.html'
    form_class = ProductForm
    success_url = '/products/'

    def dispatch(self, request, *args, **kwargs):
        if hasattr(request.user, 'role') and request.user.role.role == 'client':
            return redirect('product_list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        # Get old stock before saving
        old_stock = Product.objects.get(pk=self.object.pk).stock
        response = super().form_valid(form)
        # Log stock change if different
        new_stock = self.object.stock
        if new_stock != old_stock:
            change = new_stock - old_stock
            InventoryLog.objects.create(
                product=self.object,
                change=change,
                reason=f'Stock updated from {old_stock} to {new_stock}',
                user=self.request.user
            )
        return response

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect('product_list')

# --- Inventory Views ---

class InventoryDashboardView(LoginRequiredMixin, TemplateView):
    """Admin dashboard for tracking low stock, movements, and overall inventory status."""
    template_name = 'admin_panel/inventory_overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add company for business type
        context['company'] = Company.objects.first()
        
        # Products needing attention (Low Stock)
        # Assuming F expression or python filtering for low stock property, but since is_low_stock is a property
        # efficiently we need to iterate or add a DB field. For now, filter in python or if we added a DB field for threshold.
        # Ideally, we can annotate if we were using expression wrapper, but simple iteration for small DB is fine.
        
        products = Product.objects.all()
        low_stock_products = [p for p in products if p.is_low_stock]
        
        context['low_stock_products'] = low_stock_products
        context['total_products'] = products.count()
        context['low_stock_count'] = len(low_stock_products)
        context['out_of_stock_count'] = products.filter(stock__lte=0).count()
        
        # Recent Movements
        context['recent_logs'] = InventoryLog.objects.order_by('-timestamp')[:10]
        
        return context

class RecentActivityView(LoginRequiredMixin, TemplateView):
    template_name = 'admin_panel/inventory_activity_log.html'
    
    def dispatch(self, request, *args, **kwargs):
        if hasattr(request.user, 'role') and request.user.role.role == 'client':
            return redirect('product_list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Show all recent logs, excluding System (null user)
        context['recent_logs'] = InventoryLog.objects.filter(user__isnull=False).order_by('-timestamp')
        return context

@login_required
def stock_adjust(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        try:
            adjustment = int(request.POST.get('adjustment', 0))
            reason = request.POST.get('reason', 'Manual Adjustment')
            
            if adjustment != 0:
                product.stock += adjustment
                product.save()
                
                InventoryLog.objects.create(
                    product=product,
                    change=adjustment,
                    reason=reason,
                    user=request.user
                )
        except ValueError:
            pass # Handle invalid input gracefully
            
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'inventory_dashboard'
    return redirect(next_url)

@login_required
def clear_inventory_logs(request):
    """Clear all inventory logs"""
    InventoryLog.objects.all().delete()
    return redirect('inventory_dashboard')

# --- Reports View ---

class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = 'admin_panel/reports_overview.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report_data = get_reports_context()
        context.update(report_data)
        return context


# --- Admin Panel Views ---

class AdminPanelView(LoginRequiredMixin, TemplateView):
    """
    Comprehensive admin-only dashboard.
    Shows high-level business metrics, customer activity, and detailed financial charts.
    """
    template_name = 'admin_panel/admin_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if get_user_role_level(request.user) < 2:  # Require at least Staff
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        
        context = super().get_context_data(**kwargs)
        context['total_users'] = User.objects.count()
        context['total_invoices'] = Invoice.objects.count()
        context['total_customers'] = Customer.objects.count()
        context['total_products'] = Product.objects.count()
        
        # Revenue & Payment metrics
        context['total_revenue'] = Invoice.objects.filter(is_paid=True).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        context['paid_invoices'] = Invoice.objects.filter(is_paid=True).count()
        context['unpaid_invoices'] = Invoice.objects.filter(is_paid=False).count()
        
        # Active customers (last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        context['active_customers'] = Customer.objects.filter(
            invoice__date__gte=seven_days_ago
        ).distinct().count()
        
        # This month's revenue
        now = timezone.now()
        first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        context['this_month_revenue'] = Invoice.objects.filter(
            date__gte=first_of_month
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        # Outstanding amount (unpaid invoices total)
        context['outstanding_amount'] = Invoice.objects.filter(is_paid=False).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        # Average invoice value
        context['avg_invoice_value'] = Invoice.objects.aggregate(Avg('total_amount'))['total_amount__avg'] or 0
        
        # Collection rate (percentage of paid invoices)
        total = Invoice.objects.count()
        if total > 0:
            context['collection_rate'] = (context['paid_invoices'] / total) * 100
        else:
            context['collection_rate'] = 0
        
        # --- Chart Data ---
        # Last 6 months labels and data
        monthly_labels = []
        monthly_revenue_data = []
        monthly_invoices_data = []
        monthly_paid_data = []
        monthly_outstanding_data = []
        
        for i in range(5, -1, -1):
            month_date = now - relativedelta(months=i)
            month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + relativedelta(months=1)) - timedelta(seconds=1)
            
            monthly_labels.append(month_date.strftime('%b %Y'))
            
            # Revenue for month
            revenue = Invoice.objects.filter(
                is_paid=True,
                date__gte=month_start,
                date__lte=month_end
            ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            monthly_revenue_data.append(float(revenue))
            
            # Invoices for month
            total_inv = Invoice.objects.filter(date__gte=month_start, date__lte=month_end).count()
            paid_inv = Invoice.objects.filter(is_paid=True, date__gte=month_start, date__lte=month_end).count()
            monthly_invoices_data.append(total_inv)
            monthly_paid_data.append(paid_inv)
            
            # Outstanding for month
            outstanding = Invoice.objects.filter(
                is_paid=False,
                date__gte=month_start,
                date__lte=month_end
            ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            monthly_outstanding_data.append(float(outstanding))
        
        context['monthly_labels'] = json.dumps(monthly_labels)
        context['monthly_revenue_data'] = json.dumps(monthly_revenue_data)
        context['monthly_invoices_data'] = json.dumps(monthly_invoices_data)
        context['monthly_paid_data'] = json.dumps(monthly_paid_data)
        context['monthly_outstanding_data'] = json.dumps(monthly_outstanding_data)
        
        # Top 5 products by sales
        top_products = Product.objects.annotate(
            sales_count=Count('invoiceitem')
        ).order_by('-sales_count')[:5]
        
        context['top_product_names'] = json.dumps([p.name[:15] for p in top_products] if top_products else ['No Data'])
        context['top_product_sales'] = json.dumps([p.sales_count for p in top_products] if top_products else [0])
        
        # Top 5 customers by revenue
        top_customers = Customer.objects.annotate(
            total_revenue=Sum('invoice__total_amount')
        ).filter(total_revenue__isnull=False).order_by('-total_revenue')[:5]
        
        context['top_customer_names'] = json.dumps([c.name[:15] for c in top_customers] if top_customers else ['No Data'])
        context['top_customer_revenue'] = json.dumps([float(c.total_revenue or 0) for c in top_customers] if top_customers else [0])
        
        return context

class UserManagementView(LoginRequiredMixin, TemplateView):
    """Admin-only view to list and search all application users and their roles."""
    template_name = 'admin_panel/user_management.html'
    
    def dispatch(self, request, *args, **kwargs):
        if get_user_role_level(request.user) < 2:  # Require at least Staff
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        
        context = super().get_context_data(**kwargs)
        context['is_form'] = False
        
        # Search logic
        query = self.request.GET.get('q')
        users = User.objects.all().order_by('-date_joined')
        
        if query:
            users = users.filter(
                Q(username__icontains=query) | 
                Q(email__icontains=query)
            )
            context['search_query'] = query
            
        context['users'] = users
        context['current_user_level'] = get_user_role_level(self.request.user)
        return context

class UserCreateView(LoginRequiredMixin, TemplateView):
    """
    Complex admin view to create new users.
    Handles simultaneous creation of User, UserRole, and UserProfile records.
    """
    template_name = 'admin_panel/user_management.html'
    
    def dispatch(self, request, *args, **kwargs):
        if get_user_role_level(request.user) < 2:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_form'] = True
        context['edit_mode'] = False
        context['current_user_level'] = get_user_role_level(self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role', 'client')
        
        # Profile fields
        phone = request.POST.get('phone', '')
        company_name = request.POST.get('company_name', '')
        customer_name = request.POST.get('customer_name', '')
        contact_person = request.POST.get('contact_person', '')
        company_type = request.POST.get('company_type', '')
        address1 = request.POST.get('address1', '')
        address2 = request.POST.get('address2', '')
        landmark = request.POST.get('landmark', '')
        pincode = request.POST.get('pincode', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        country = request.POST.get('country', 'India')
        address = request.POST.get('address', '')  # Legacy field
        
        if get_user_role_level(request.user) < 2:
            messages.error(request, "Permission denied.")
            return redirect('user_management')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, f"User with username '{username}' already exists.")
            return redirect('user_create')

        if email and User.objects.filter(email=email).exists():
            messages.error(request, f"User with email '{email}' already exists.")
            return redirect('user_create')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=(role == 'admin'),
            is_superuser=(role == 'admin')
        )
        
        from .models import UserRole, UserProfile
        UserRole.objects.create(user=user, role=role)
        UserProfile.objects.create(
            user=user, 
            phone=phone, 
            company_name=company_name,
            customer_name=customer_name,
            contact_person=contact_person,
            company_type=company_type,
            address1=address1,
            address2=address2,
            landmark=landmark,
            pincode=pincode,
            city=city,
            state=state,
            country=country,
            address=address
        )
        
        # Log Activity
        from .models import ActivityLog
        ActivityLog.objects.create(
            user=request.user,
            action='CREATE',
            model_name='User',
            object_repr=username,
            details=f"Created new user {username} with role {role}"
        )
        
        return redirect('user_management')

class UserUpdateView(LoginRequiredMixin, TemplateView):
    """
    Complex admin view to edit existing users.
    Syncs changes across User, UserRole, and UserProfile models.
    """
    template_name = 'admin_panel/user_management.html'
    
    def dispatch(self, request, *args, **kwargs):
        if get_user_role_level(request.user) < 2:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get('pk')
        target_user = get_object_or_404(User, pk=user_id)
        
        # Get role safely
        try:
            current_role = target_user.role.role
        except UserRole.DoesNotExist:
            current_role = 'admin' if target_user.is_staff else 'client'
            
        context['is_form'] = True
        context['edit_mode'] = True
        context['target_user'] = target_user
        context['current_role'] = current_role
        context['current_user_level'] = get_user_role_level(self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        user_id = self.kwargs.get('pk')
        target_user = get_object_or_404(User, pk=user_id)
        
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role', 'client')
        
        # Profile fields
        phone = request.POST.get('phone', '')
        company_name = request.POST.get('company_name', '')
        customer_name = request.POST.get('customer_name', '')
        contact_person = request.POST.get('contact_person', '')
        company_type = request.POST.get('company_type', '')
        address1 = request.POST.get('address1', '')
        address2 = request.POST.get('address2', '')
        landmark = request.POST.get('landmark', '')
        pincode = request.POST.get('pincode', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        country = request.POST.get('country', 'India')
        address = request.POST.get('address', '')  # Legacy field
        
        if get_user_role_level(request.user) < 2:
            messages.error(request, "Permission denied.")
            return redirect('user_management')

        # Check uniqueness but exclude current user
        if User.objects.filter(username=username).exclude(pk=user_id).exists():
            messages.error(request, f"User with username '{username}' already exists.")
            return redirect('user_update', pk=user_id)
            
        if email and User.objects.filter(email=email).exclude(pk=user_id).exists():
            messages.error(request, f"User with email '{email}' already exists.")
            return redirect('user_update', pk=user_id)
        
        # Update basic fields
        target_user.username = username
        target_user.email = email
        
        # Update password only if provided
        if password and password.strip():
            target_user.set_password(password)
            
        # Update Status/Role logic
        is_admin = (role == 'admin')
        target_user.is_staff = is_admin
        target_user.is_superuser = is_admin
        target_user.save()
        
        # Update UserRole
        from .models import UserRole, UserProfile
        user_role, created = UserRole.objects.get_or_create(user=target_user)
        user_role.role = role
        user_role.save()
        
        # Update UserProfile
        user_profile, created = UserProfile.objects.get_or_create(user=target_user)
        user_profile.phone = phone
        user_profile.company_name = company_name
        user_profile.customer_name = customer_name
        user_profile.contact_person = contact_person
        user_profile.company_type = company_type
        user_profile.address1 = address1
        user_profile.address2 = address2
        user_profile.landmark = landmark
        user_profile.pincode = pincode
        user_profile.city = city
        user_profile.state = state
        user_profile.country = country
        user_profile.address = address
        user_profile.save()
        
        # Log Activity
        from .models import ActivityLog
        ActivityLog.objects.create(
            user=request.user,
            action='UPDATE',
            model_name='User',
            object_repr=target_user.username,
            details=f"Updated user {target_user.username} (Role: {role})"
        )
        
        return redirect('user_management')

@login_required
def user_toggle_status(request, pk):
    """Security utility to activate or deactivate a user account with audit logging."""
    if get_user_role_level(request.user) < 2:
        return redirect('dashboard')
        
    user = get_object_or_404(User, pk=pk)
    
    # Prevent deactivating self
    if user.id == request.user.id:
        return redirect('user_management')
        
    user.is_active = not user.is_active
    user.save()
    
    # Log Activity
    from .models import ActivityLog
    status_msg = "Activated" if user.is_active else "Deactivated"
    ActivityLog.objects.create(
        user=request.user,
        action='UPDATE',
        model_name='User',
        object_repr=user.username,
        details=f"{status_msg} user {user.username}"
    )
    
    return redirect('user_management')

class UserActivityView(LoginRequiredMixin, TemplateView):
    """View to display detailed audit logs for a specific user's actions."""
    template_name = 'admin_panel/user_activity_log.html'
    
    def dispatch(self, request, *args, **kwargs):
        if get_user_role_level(request.user) < 2:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get('pk')
        target_user = get_object_or_404(User, pk=user_id)
        
        context['target_user'] = target_user
        context['activities'] = ActivityLog.objects.filter(user=target_user).order_by('-timestamp')
        return context

@login_required
def user_delete(request, pk):
    current_level = get_user_role_level(request.user)
    
    # Only admins can delete users
    if current_level < 2:
        return redirect('dashboard')
    
    user_to_delete = get_object_or_404(User, pk=pk)
    target_level = get_user_role_level(user_to_delete)
    
    # Can only delete users with LOWER role level (not equal)
    # Cannot delete yourself
    if user_to_delete.id != request.user.id and target_level < current_level:
        username = user_to_delete.username
        user_to_delete.delete()
        
        # Log Activity
        ActivityLog.objects.create(
            user=request.user,
            action='DELETE',
            model_name='User',
            object_repr=username,
            details=f"Deleted user {username}"
        )
    
    return redirect('user_management')


@login_required
def send_user_credentials(request, pk):
    """
    Security utility to generate a temporary password and send a secure, 
    professional HTML onboarding email with login and reset links.
    """
    """Send login credentials to a user via email"""
    if get_user_role_level(request.user) < 2:
        messages.error(request, "Permission denied.")
        return redirect('user_management')
    
    target_user = get_object_or_404(User, pk=pk)
    
    from django.core.mail import EmailMessage
    from django.conf import settings
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes
    import random
    import string
    
    # Generate a temporary password
    temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    
    # Set the temporary password
    target_user.set_password(temp_password)
    target_user.save()
    
    # Generate password reset token and link
    uid = urlsafe_base64_encode(force_bytes(target_user.pk))
    token = default_token_generator.make_token(target_user)
    reset_link = f"{request.scheme}://{request.get_host()}/accounts/reset/{uid}/{token}/"
    
    # Get company details
    company = Company.objects.first()
    company_name = company.name if company else 'Chargebee Billing System'
    
    # Create professional HTML email
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
            }}
            .email-container {{
                max-width: 600px;
                margin: 20px auto;
                background-color: #ffffff;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
                color: #ffffff;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: 600;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .content h2 {{
                color: #1f2937;
                font-size: 20px;
                margin-top: 0;
                margin-bottom: 20px;
            }}
            .credentials-box {{
                background-color: #f8f9fa;
                border-left: 4px solid #3b82f6;
                padding: 20px;
                margin: 25px 0;
                border-radius: 4px;
            }}
            .credential-row {{
                display: flex;
                padding: 8px 0;
                border-bottom: 1px solid #e5e7eb;
            }}
            .credential-row:last-child {{
                border-bottom: none;
            }}
            .credential-label {{
                font-weight: 600;
                color: #374151;
                min-width: 140px;
            }}
            .credential-value {{
                color: #1f2937;
                font-family: 'Courier New', monospace;
                word-break: break-all;
            }}
            .password-highlight {{
                background-color: #fef3c7;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: 600;
                color: #92400e;
            }}
            .button {{
                display: inline-block;
                background-color: #3b82f6;
                color: #ffffff !important;
                text-decoration: none;
                padding: 12px 30px;
                border-radius: 6px;
                font-weight: 600;
                margin: 20px 0;
            }}
            .warning-box {{
                background-color: #fef2f2;
                border-left: 4px solid #ef4444;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .warning-box strong {{
                color: #991b1b;
            }}
            .footer {{
                background-color: #f9fafb;
                padding: 20px 30px;
                text-align: center;
                border-top: 1px solid #e5e7eb;
                color: #6b7280;
                font-size: 13px;
            }}
            .footer p {{
                margin: 5px 0;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>{company_name}</h1>
                <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.9;">Account Credentials</p>
            </div>
            
            <div class="content">
                <h2>Welcome, {target_user.first_name or target_user.username}!</h2>
                
                <p>Your account has been successfully created in the {company_name}. Below are your login credentials:</p>
                
                <div class="credentials-box">
                    <div class="credential-row">
                        <span class="credential-label">Username:</span>
                        <span class="credential-value">{target_user.username}</span>
                    </div>
                    <div class="credential-row">
                        <span class="credential-label">Email:</span>
                        <span class="credential-value">{target_user.email}</span>
                    </div>
                    <div class="credential-row">
                        <span class="credential-label">Temporary Password:</span>
                        <span class="credential-value"><span class="password-highlight">{temp_password}</span></span>
                    </div>
                    <div class="credential-row">
                        <span class="credential-label">Login URL:</span>
                        <span class="credential-value">{request.scheme}://{request.get_host()}/accounts/login/</span>
                    </div>
                </div>
                
                <center>
                    <a href="{request.scheme}://{request.get_host()}/accounts/login/" class="button">
                        Login to Your Account
                    </a>
                    <br>
                    <a href="{reset_link}" class="button" style="background-color: #059669; margin-top: 10px;">
                        Change Password Now
                    </a>
                </center>
                
                <div class="warning-box">
                    <strong>⚠️ Important Security Notice</strong>
                    <p style="margin: 8px 0 0 0;">You can either login with the temporary password above, or click "Change Password Now" to set your own password immediately. For security, we recommend changing your password as soon as possible.</p>
                </div>
                
                <p style="margin-top: 25px;">If you have any questions or need assistance, please don't hesitate to contact your system administrator.</p>
                
                <p>Best regards,<br>
                <strong>{company_name} Team</strong></p>
            </div>
            
            <div class="footer">
                <p>This is an automated message. Please do not reply to this email.</p>
                <p>© {company_name} · All rights reserved</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    subject = f'Your Login Credentials - {company_name}'
    
    try:
        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[target_user.email],
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)
        
        ActivityLog.objects.create(
            user=request.user, 
            action='UPDATE', 
            model_name='User', 
            object_id=target_user.id, 
            object_repr=target_user.username, 
            details=f"Sent credentials email to {target_user.email}"
        )
        from django.contrib import messages
        messages.success(request, f"Credentials sent successfully to {target_user.email}")
    except Exception as e:
        ActivityLog.objects.create(
            user=request.user, 
            action='UPDATE', 
            model_name='User', 
            object_id=target_user.id, 
            object_repr=target_user.username, 
            details=f"Failed to send credentials email: {str(e)}"
        )
        from django.contrib import messages
        messages.error(request, f"Failed to send credentials: {str(e)}")
    
    return redirect('user_management')

class CompanySettingsView(LoginRequiredMixin, TemplateView):
    """
    Superuser-only view to manage legal company details, bank info, 
    and branding (logo).
    """
    template_name = 'admin_panel/company_settings.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company'] = Company.objects.first()
        return context
    
    def post(self, request, *args, **kwargs):
        company = Company.objects.first()
        if not company:
            company = Company()
            
        company.name = request.POST.get('name')
        company.address = request.POST.get('address')
        company.phone = request.POST.get('phone')
        company.email = request.POST.get('email')
        
        # Save new fields
        company.owner_name = request.POST.get('owner_name', '')
        company.company_type = request.POST.get('company_type', '')
        company.pan_number = request.POST.get('pan_number', '')
        company.state = request.POST.get('state', '')
        company.city = request.POST.get('city', '')
        company.pincode = request.POST.get('pincode', '')

        company.tax_id = request.POST.get('tax_id')
        company.website = request.POST.get('website')
        company.bank_name = request.POST.get('bank_name')
        company.account_number = request.POST.get('account_number')
        company.ifsc_code = request.POST.get('ifsc_code')
        company.swift_code = request.POST.get('swift_code')
        company.terms_and_conditions = request.POST.get('terms_and_conditions')
        company.footer_text = request.POST.get('footer_text')
        
        if 'logo' in request.FILES:
            company.logo = request.FILES['logo']
        elif request.POST.get('clear_logo') == 'true':
            if company.logo:
                company.logo.delete(save=False)
            company.logo = None
        
        company.save()
        return redirect('company_settings')


@login_required
def company_settings_reset(request):
    """Reset all company settings back to defaults"""
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    if request.method == 'POST':
        company = Company.objects.first()
        if company:
            # Delete the logo file if it exists
            if company.logo:
                company.logo.delete(save=False)
            company.delete()
        
        # Log the reset action
        ActivityLog.objects.create(
            user=request.user,
            action='DELETE',
            model_name='Company',
            object_repr='Company Settings',
            details='Reset all company settings to defaults'
        )
    
    return redirect('company_settings')


# Razorpay Payment Views are now in payments.py


# --- Business Inventory Population ---
@login_required
def add_all_business_products(request):
    """Add business category products to inventory, optionally filtered by type"""
    from .populate_inventory import populate_inventory
    import json
    
    if request.method == 'POST':
        try:
            business_type = request.POST.get('business_type', '')
            
            # Call populate function directly
            if business_type:
                count, output = populate_inventory(business_type=business_type)
                message = f'{business_type.title()} products added successfully!'
            else:
                count, output = populate_inventory()
                message = 'All business products added successfully!'
            
            return HttpResponse(
                json.dumps({
                    'success': True,
                    'message': message,
                    'output': output
                }),
                content_type='application/json'
            )
        except Exception as e:
            return HttpResponse(
                json.dumps({
                    'success': False,
                    'error': str(e)
                }),
                content_type='application/json'
            )
    
    return HttpResponse(
        json.dumps({'success': False, 'error': 'Invalid request method'}),
        content_type='application/json'
    )

@login_required
def remove_all_products(request):
    """Remove all products from inventory"""
    import json
    from .models import Product, InventoryLog
    from django.db import connection
    
    if request.method == 'POST':
        try:
            # Check permissions - only admin/owner can delete
            if hasattr(request.user, 'role') and request.user.role.role == 'client':
                return HttpResponse(
                    json.dumps({'success': False, 'error': 'Permission denied'}),
                    content_type='application/json',
                    status=403
                )
            
            count = Product.objects.count()
            
            # Use raw SQL to delete, bypassing Django signals completely
            with connection.cursor() as cursor:
                # First, set product_id to NULL in inventory logs (preserve audit trail)
                cursor.execute("UPDATE billing_inventorylog SET product_id = NULL")
                # Then delete invoice items that reference products
                cursor.execute("DELETE FROM billing_invoiceitem")
                # Finally delete all products
                cursor.execute("DELETE FROM billing_product")
            
            return HttpResponse(
                json.dumps({
                    'success': True,
                    'message': f'Successfully removed {count} products.'
                }),
                content_type='application/json'
            )
        except Exception as e:
            return HttpResponse(
                json.dumps({
                    'success': False,
                    'error': str(e)
                }),
                content_type='application/json'
            )
            
    return HttpResponse(
        json.dumps({'success': False, 'error': 'Invalid request method'}),
        content_type='application/json'
    )

# --- Expense Views ---

from .models import Expense, ProductCategory, Quotation, QuotationItem
from .forms import ExpenseForm

class ExpenseListView(LoginRequiredMixin, ListView):
    """Admin-only view to track and filter business expenses by category."""
    model = Expense
    template_name = 'admin_panel/expense_management.html'
    context_object_name = 'expenses'
    
    def dispatch(self, request, *args, **kwargs):
        if hasattr(request.user, 'role') and request.user.role.role == 'client':
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) | Q(description__icontains=q) | Q(reference__icontains=q)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['categories'] = Expense.CATEGORY_CHOICES
        
        # Summary stats
        expenses = self.get_queryset()
        total_exp = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_expenses'] = indian_currency_format(total_exp)
        context['expense_count'] = expenses.count()
        
        # This month
        now = datetime.now()
        this_month = expenses.filter(date__month=now.month, date__year=now.year)
        m_total = this_month.aggregate(Sum('amount'))['amount__sum'] or 0
        context['monthly_total'] = indian_currency_format(m_total)
        
        # Format individual expenses
        for exp in context['expenses']:
            exp.formatted_amount = indian_currency_format(exp.amount)
            
        return context


class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    template_name = 'admin_panel/expense_management.html'
    form_class = ExpenseForm
    success_url = '/expenses/'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view_mode'] = 'form'
        return context


class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Expense
    template_name = 'admin_panel/expense_management.html'
    form_class = ExpenseForm
    success_url = '/expenses/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view_mode'] = 'form'
        return context


@login_required
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    expense.delete()
    return redirect('expense_list')



# --- Payment Reminder ---

@login_required
def send_payment_reminder(request, pk):
    """
    Utility to send a personalized payment reminder email for unpaid invoices.
    Runs asynchronously in a background thread.
    """
    """Send a payment reminder email for an unpaid invoice"""
    from django.core.mail import send_mail
    from django.contrib import messages
    
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if invoice.is_paid:
        messages.info(request, "This invoice is already paid.")
        return redirect('invoice_detail', pk=pk)
        
    invoice.reminder_sent = True
    invoice.save(update_fields=['reminder_sent'])
    
    messages.success(request, f"Payment reminder recorded for Dashboard!")
    
    return redirect('invoice_detail', pk=pk)


# --- Customer Statement ---

@login_required
def customer_statement(request, pk):
    """Generates a comprehensive financial statement for a customer, showing all billing history."""
    """Show full transaction history for a customer"""
    customer = get_object_or_404(Customer, pk=pk)
    invoices = Invoice.objects.filter(customer=customer).order_by('-date')
    
    total_billed = invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_paid = Transaction.objects.filter(invoice__customer=customer).aggregate(Sum('amount'))['amount__sum'] or 0
    total_outstanding = total_billed - total_paid
    
    context = {
        'customer': customer,
        'invoices': invoices,
        'total_billed': indian_currency_format(total_billed),
        'total_paid': indian_currency_format(total_paid),
        'total_outstanding': indian_currency_format(total_outstanding),
    }
    return render(request, 'admin_panel/customer_statement.html', context)


# --- API Standard Views (Moved from api_views.py) ---
from rest_framework import viewsets
from .serializers import CustomerSerializer, ProductSerializer, InvoiceSerializer, TransactionSerializer

class CustomerViewSet(viewsets.ModelViewSet):
    """API endpoint for Customer CRUD operations."""
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

@login_required
def clear_reminders(request):
    """Clear payment reminders for the current client"""
    from django.contrib import messages
    if request.method == 'POST':
        # Find all unpaid invoices with reminders for this user's assigned customers
        from .permissions import filter_invoices_by_role
        invoices = filter_invoices_by_role(request.user, Invoice.objects.filter(is_paid=False, reminder_sent=True))
        
        # Clear the reminder flag
        for invoice in invoices:
            if hasattr(request.user, 'role') and request.user.role.role == 'client':
                invoice.reminder_sent = False
                invoice.save(update_fields=['reminder_sent'])
                
        messages.success(request, "Payment reminders cleared.")
    
    return redirect('dashboard')
