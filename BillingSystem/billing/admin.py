"""
Django administration configuration for the billing app models.
Defines list views, filters, and custom admin actions.
"""
from django.contrib import admin
from .models import (
	Company, Customer, Product, Invoice, InvoiceItem, Transaction,
	UserRole, UserProfile, CustomerAssignment, ActivityLog, RazorpayPayment, InventoryLog
)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
	list_display = ('name', 'phone', 'email')
	search_fields = ('name', 'email', 'phone')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
	list_display = ('name', 'email', 'phone', 'created_at')
	search_fields = ('name', 'email', 'phone')
	list_filter = ('created_at',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = ('name', 'company', 'price', 'stock', 'is_low_stock', 'hsn_code')
	search_fields = ('name', 'hsn_code', 'company__name')
	list_editable = ('price', 'stock')
	list_filter = ('company',)

	def is_low_stock(self, obj):
		return obj.is_low_stock
	is_low_stock.boolean = True


class InvoiceItemInline(admin.TabularInline):
	model = InvoiceItem
	extra = 0
	readonly_fields = ('gst_amount',)


class TransactionInline(admin.TabularInline):
	model = Transaction
	extra = 0
	readonly_fields = ('date',)
	fields = ('amount', 'payment_method', 'date')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
	list_display = ('id', 'customer', 'company', 'date', 'total_amount', 'is_paid')
	list_filter = ('is_paid', 'date', 'company')
	search_fields = ('customer__name', 'id')
	inlines = (InvoiceItemInline, TransactionInline)
	readonly_fields = ('qr_code',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
	list_display = ('invoice_id', 'customer_name', 'invoice_status', 'amount', 'payment_method', 'date', 'balance_due')
	search_fields = ('invoice__id', 'invoice__customer__name')
	list_filter = ('payment_method', 'date', 'invoice__is_paid')
	actions = ['mark_invoice_paid']
	
	def invoice_id(self, obj):
		return f"Invoice #{obj.invoice.id}"
	invoice_id.short_description = 'Invoice'
	
	def customer_name(self, obj):
		return obj.invoice.customer.name
	customer_name.short_description = 'Customer'
	
	def invoice_status(self, obj):
		if obj.invoice.is_paid:
			return "✅ PAID"
		else:
			return "❌ UNPAID"
	invoice_status.short_description = 'Status'
	
	def balance_due(self, obj):
		return f"₹{obj.invoice.balance_due:,.2f}"
	balance_due.short_description = 'Balance Due'

	def mark_invoice_paid(self, request, queryset):
		"""Admin action: update related invoices' payment status after applying selected transactions."""
		invoices = set(t.invoice for t in queryset)
		updated = 0
		for inv in invoices:
			inv.update_payment_status()
			updated += 1
		self.message_user(request, f"Updated payment status for {updated} invoice(s).")
	mark_invoice_paid.short_description = 'Update payment status for selected transactions\' invoices'


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
	list_display = ('user', 'role')
	search_fields = ('user__username', 'role')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'department', 'employee_id', 'supervisor')
	search_fields = ('user__username', 'employee_id')


@admin.register(CustomerAssignment)
class CustomerAssignmentAdmin(admin.ModelAdmin):
	list_display = ('user', 'customer', 'assigned_date', 'assigned_by')
	search_fields = ('user__username', 'customer__name')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
	list_display = ('user', 'action', 'model_name', 'object_id', 'timestamp')
	list_filter = ('action', 'model_name')
	search_fields = ('user__username', 'model_name', 'object_repr')


@admin.register(RazorpayPayment)
class RazorpayPaymentAdmin(admin.ModelAdmin):
	list_display = ('razorpay_order_id', 'invoice', 'amount_display', 'status', 'created_at', 'updated_at')
	list_filter = ('status', 'created_at', 'updated_at')
	search_fields = ('razorpay_order_id', 'razorpay_payment_id', 'invoice__id')
	readonly_fields = ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'created_at', 'updated_at')
	
	def amount_display(self, obj):
		return f"₹{obj.amount / 100:.2f}"
	amount_display.short_description = 'Amount'

@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
	list_display = ('product', 'change', 'reason', 'user', 'timestamp')
	list_filter = ('timestamp', 'reason', 'user')
	search_fields = ('product__name', 'reason')

