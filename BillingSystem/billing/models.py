"""
Database models for the Billing system, including Company settings,
Customers, Products, Invoices, Transactions, and Inventory tracking.
"""
from django.db import models, connection
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.validators import MinValueValidator
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image, ImageDraw
from django.utils import timezone
from datetime import timedelta

class Company(models.Model):
    """Stores global company settings and billing details used across the system."""
    name = models.CharField(max_length=100, default="My Company")
    address = models.TextField(default="123 Business Rd, Tech City")
    phone = models.CharField(max_length=20, default="+1 234 567 890")
    email = models.EmailField(default="contact@mycompany.com")
    logo = models.ImageField(upload_to='company/', blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, default="", help_text="Tax ID / GSTIN")
    website = models.URLField(blank=True, default="")
    
    # New Fields
    owner_name = models.CharField(max_length=100, blank=True, default="")
    company_type = models.CharField(max_length=50, blank=True, default="")
    pan_number = models.CharField(max_length=20, blank=True, default="")
    state = models.CharField(max_length=50, blank=True, default="")
    city = models.CharField(max_length=50, blank=True, default="")
    pincode = models.CharField(max_length=10, blank=True, default="")
    
    # Bank Details
    bank_name = models.CharField(max_length=100, blank=True, default="")
    account_number = models.CharField(max_length=50, blank=True, default="")
    ifsc_code = models.CharField(max_length=20, blank=True, default="")
    swift_code = models.CharField(max_length=20, blank=True, default="")
    
    terms_and_conditions = models.TextField(blank=True, default="", help_text="Default Terms & Conditions for new invoices")
    
    footer_text = models.TextField(blank=True, default="", help_text="Text to display at the bottom of invoices")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Company"

class Customer(models.Model):
    """Represents a client/customer who receives invoices."""
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, default="")
    
    # Company Details
    company_name = models.CharField(max_length=200, blank=True, default="")
    contact_person = models.CharField(max_length=200, blank=True, default="")
    company_type = models.CharField(max_length=50, blank=True, default="")
    
    # Address Information
    address1 = models.CharField(max_length=255, blank=True, default="")
    address2 = models.CharField(max_length=255, blank=True, default="")
    landmark = models.CharField(max_length=100, blank=True, default="")
    pincode = models.CharField(max_length=20, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    state = models.CharField(max_length=100, blank=True, default="")
    country = models.CharField(max_length=100, blank=True, default='India')
    
    address = models.TextField(blank=True, default="") # Legacy field
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    """Represents an item or service that can be billed on an invoice."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    hsn_code = models.CharField(max_length=20, blank=True, default="8517")
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, validators=[MinValueValidator(0)]) # e.g. 18.00 means 18%
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, validators=[MinValueValidator(0)], help_text="Discount percentage")
    
    # Smart Inventory Fields
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='products')
    category = models.ForeignKey('ProductCategory', on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    low_stock_threshold = models.IntegerField(default=5, help_text="Alert when stock falls below this level")

    def __str__(self):
        return self.name
    
    @property
    def is_low_stock(self):
        return self.stock <= self.low_stock_threshold


class Invoice(models.Model):
    """
    Represents a billing document sent to a customer.
    Tracks total amount, payment status, and metadata.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='invoices')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    
    # New Fields
    dispatch_through = models.CharField(max_length=100, blank=True, default="")
    due_date = models.DateField(null=True, blank=True)
    payment_terms = models.TextField(blank=True, default="", help_text="e.g. Net 30, Payment Type")
    payment_note = models.TextField(blank=True, default="")
    terms_and_conditions = models.TextField(blank=True, default="")
    document_note = models.TextField(blank=True, default="")
    bank_details = models.TextField(blank=True, default="", help_text="Override bank details for this invoice")
    
    # Email tracking
    emailed_at = models.DateTimeField(null=True, blank=True, help_text="Last time this invoice was emailed")
    emailed_to = models.EmailField(blank=True, default="", help_text="Email address the invoice was sent to")
    reminder_sent = models.BooleanField(default=False, help_text="Indicates if a payment reminder has been sent by the admin")
    
    @property
    def amount_paid(self):
        """Calculates the total amount paid toward this invoice from all transactions."""
        return sum(t.amount for t in self.transactions.all())

    @property
    def balance_due(self):
        """Calculates the remaining balance owed on this invoice."""
        return self.total_amount - self.amount_paid

    def update_payment_status(self):
        """Updates the is_paid boolean based on the current balance due."""
        if self.balance_due <= 0:
            self.is_paid = True
        else:
            self.is_paid = False
        self.save(update_fields=['is_paid'])

    def save(self, *args, **kwargs):
        # Auto-set Due Date to 30 days if not provided
        if not self.due_date:
            # For new invoices, use current time. For existing, use created date.
            base_date = self.date if self.date else timezone.now()
            self.due_date = base_date.date() + timedelta(days=30)

        # Save first to ensure we have an ID and related items
        super().save(*args, **kwargs)
        
        # Simplified QR Data for better scan-ability
        qr_data = f"Invoice: #{self.id}\n"
        qr_data += f"Date: {self.date.strftime('%d/%m/%Y')}\n"
        qr_data += f"Customer: {self.customer.name}\n"
        qr_data += f"Amount: ₹{self.total_amount}\n"
        qr_data += f"Status: {'PAID' if self.is_paid else 'UNPAID'}"
        
        # Optimize QR code image settings
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Generate QR code image
        qrcode_img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to file
        buffer = BytesIO()
        qrcode_img.save(buffer, format='PNG')
        fname = f'qr_code-{self.id}.png'
        
        self.qr_code.save(fname, File(buffer), save=False)
        buffer.close()
        
        # Call super again to save the qr_code field without recursion
        super().save(update_fields=['qr_code'])

    def __str__(self):
        return f"Invoice #{self.id} - {self.customer.name}"

class InvoiceFeedback(models.Model):
    """Client-Admin communication thread for specific invoices"""
    invoice = models.ForeignKey(Invoice, related_name='feedbacks', on_delete=models.CASCADE)
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Feedback on Invoice #{self.invoice.id} by {self.user.username}"

class InvoiceItem(models.Model):
    """Represents a specific product and its quantity/pricing on an invoice."""
    invoice = models.ForeignKey(Invoice, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2) # Unit price
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.product.price
        if not self.gst_rate:
            self.gst_rate = self.product.gst_rate
        
        # Calculate GST Amount
        # Formula: (Price * Qty) * (GST / 100)
        taxable_value = self.price * self.quantity
        self.gst_amount = (taxable_value * self.gst_rate) / 100
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def subtotal(self):
        """Subtotal before tax (Rate × Qty)"""
        return self.price * self.quantity
    
    @property
    def total_with_tax(self):
        taxable = self.price * self.quantity
        return taxable + self.gst_amount


class Transaction(models.Model):
    """Records a specific payment received for an invoice."""
    invoice = models.ForeignKey(Invoice, related_name='transactions', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, choices=[('CASH', 'Cash'), ('ONLINE', 'Online')])

    def __str__(self):
        return f"Payment of {self.amount} for Invoice #{self.invoice.id}"


class RazorpayPayment(models.Model):
    """Track Razorpay payment orders and transactions"""
    
    STATUS_CHOICES = [
        ('CREATED', 'Created'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('PENDING', 'Pending'),
    ]
    
    invoice = models.ForeignKey(Invoice, related_name='razorpay_payments', on_delete=models.CASCADE)
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    amount = models.IntegerField(help_text="Amount in paise (smallest currency unit)")
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CREATED')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def verify_signature(self, razorpay_signature):
        """Verify Razorpay payment signature for security"""
        import hmac
        import hashlib
        from django.conf import settings
        
        # Create signature verification string
        message = f"{self.razorpay_order_id}|{self.razorpay_payment_id}"
        
        # Generate expected signature
        expected_signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, razorpay_signature)
    
    def __str__(self):
        return f"Razorpay Payment {self.razorpay_order_id} - {self.status}"


class UserRole(models.Model):
    """
    Extensions to the User model to support a custom role hierarchy.
    Supported roles: 'admin' and 'client'.
    """
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('client', 'Client'),
    ]
    
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='role')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    @property
    def role_level(self):
        """Return numeric level for hierarchy comparison (higher = more power)"""
        levels = {'admin': 2, 'client': 1}
        return levels.get(self.role, 1)

class UserProfile(models.Model):
    """Stores extended contact and company information for system users."""
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='profile')
    
    # Contact Information
    phone = models.CharField(max_length=20, blank=True)
    
    # Company Details
    company_name = models.CharField(max_length=200, blank=True)
    customer_name = models.CharField(max_length=200, blank=True)
    contact_person = models.CharField(max_length=200, blank=True)
    company_type = models.CharField(max_length=50, blank=True)
    
    # Address Information
    address1 = models.CharField(max_length=255, blank=True)
    address2 = models.CharField(max_length=255, blank=True)
    landmark = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True, default='India')
    
    # Legacy field (kept for backward compatibility)
    address = models.TextField(blank=True)
    
    # Additional fields
    department = models.CharField(max_length=100, blank=True)
    employee_id = models.CharField(max_length=50, blank=True)
    supervisor = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_users')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Profile: {self.user.username}"

class CustomerAssignment(models.Model):
    """Assign customers to specific users for access control"""
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='customer_assignments')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='assignments')
    assigned_date = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='assignments_made')
    
    class Meta:
        unique_together = ('user', 'customer')
    
    def __str__(self):
        return f"{self.user.username} -> {self.customer.name}"

class ActivityLog(models.Model):
    """Audit trail for all system actions"""
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
    ]
    
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='activity_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.IntegerField(null=True, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user} - {self.action} {self.model_name} at {self.timestamp}"


# Signals for ID sequence management
@receiver(post_delete, sender=Invoice)
def reset_invoice_id_sequence(sender, instance, **kwargs):
    """
    Sync the auto-increment counter with the maximum ID after every deletion.
    This ensures no gaps are left at the end of the sequence and it starts from 1 if empty.
    """
    from django.db.models import Max
    max_id = sender.objects.aggregate(Max('id'))['id__max'] or 0
    
    with connection.cursor() as cursor:
        if connection.vendor == 'sqlite':
            # Check if table exists in sequence table first
            cursor.execute("SELECT name FROM sqlite_sequence WHERE name='billing_invoice'")
            if cursor.fetchone():
                cursor.execute("UPDATE sqlite_sequence SET seq = %s WHERE name = 'billing_invoice'", [max_id])
            elif max_id == 0:
                # If table empty and no sequence record, this is fine, it will start at 1 anyway
                pass
        elif connection.vendor == 'postgresql':
            cursor.execute(f"SELECT setval('billing_invoice_id_seq', %s, false)", [max_id + 1])


@receiver(post_delete, sender=Product)
def reset_product_id_sequence(sender, instance, **kwargs):
    from django.db.models import Max
    max_id = sender.objects.aggregate(Max('id'))['id__max'] or 0
    with connection.cursor() as cursor:
        if connection.vendor == 'sqlite':
            cursor.execute("SELECT name FROM sqlite_sequence WHERE name='billing_product'")
            if cursor.fetchone():
                cursor.execute("UPDATE sqlite_sequence SET seq = %s WHERE name = 'billing_product'", [max_id])

class InventoryLog(models.Model):
    """Audit log for stock changes on products."""
    """Audit trail for stock adjustments"""
    product = models.ForeignKey(Product, related_name='inventory_logs', on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=100, blank=True, help_text="Product name cached for deleted products")
    change = models.IntegerField(help_text="Positive for addition, negative for deduction")
    reason = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        product_name = self.product.name if self.product else self.product_name
        return f"{product_name}: {self.change} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"



@receiver(post_delete, sender=Customer)
def reset_customer_id_sequence(sender, instance, **kwargs):
    from django.db.models import Max
    max_id = sender.objects.aggregate(Max('id'))['id__max'] or 0
    with connection.cursor() as cursor:
        if connection.vendor == 'sqlite':
            cursor.execute("SELECT name FROM sqlite_sequence WHERE name='billing_customer'")
            if cursor.fetchone():
                cursor.execute("UPDATE sqlite_sequence SET seq = %s WHERE name = 'billing_customer'", [max_id])


class Expense(models.Model):
    """Track business expenses"""
    CATEGORY_CHOICES = [
        ('RENT', 'Rent'),
        ('UTILITIES', 'Utilities'),
        ('SALARY', 'Salary'),
        ('SUPPLIES', 'Office Supplies'),
        ('TRANSPORT', 'Transport'),
        ('MARKETING', 'Marketing'),
        ('MAINTENANCE', 'Maintenance'),
        ('INSURANCE', 'Insurance'),
        ('TAX', 'Taxes & Fees'),
        ('OTHER', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OTHER')
    description = models.TextField(blank=True)
    date = models.DateField()
    reference = models.CharField(max_length=100, blank=True, help_text="Receipt or reference number")
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.title} - ₹{self.amount}"


class ProductCategory(models.Model):
    """Categories for products (e.g. Services, Hardware)."""
    """Organize products into categories"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Product Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Quotation(models.Model):
    """Quotation/Estimate before invoice"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('CONVERTED', 'Converted to Invoice'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='quotations')
    date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True)
    converted_invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='source_quotation')
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Quote #{self.id} - {self.customer.name}"


class QuotationItem(models.Model):
    """Line items for a quotation"""
    quotation = models.ForeignKey(Quotation, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.product.price
        if not self.gst_rate:
            self.gst_rate = self.product.gst_rate
        taxable_value = self.price * self.quantity
        self.gst_amount = (taxable_value * self.gst_rate) / 100
        super().save(*args, **kwargs)
    
    @property
    def subtotal(self):
        return self.price * self.quantity
    
    @property
    def total_with_tax(self):
        return self.subtotal + self.gst_amount
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

