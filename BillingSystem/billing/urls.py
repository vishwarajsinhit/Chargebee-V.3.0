"""
URL routing for the Billing application.
Defines paths for Web UI, API, and Authentication views.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.contrib.auth import views as auth_views
from .views import (
    DashboardView, InvoiceListView, InvoiceDetailView, InvoiceCreateView, InvoiceUpdateView, invoice_delete,
    CustomerListView, CustomerCreateView, CustomerUpdateView, customer_delete,
    ProductListView, ProductCreateView, ProductUpdateView, product_delete,
    ReportsView,
    AdminPanelView, UserManagementView, UserCreateView, UserUpdateView, UserActivityView, user_delete, send_user_credentials, user_toggle_status, CompanySettingsView, company_settings_reset,
    generate_pdf, record_payment, generate_reports_pdf, email_invoice, submit_invoice_feedback,
    ClientProfileView,
    InventoryDashboardView, RecentActivityView, stock_adjust, clear_inventory_logs, add_all_business_products, remove_all_products,
    ExpenseListView, ExpenseCreateView, ExpenseUpdateView, expense_delete,
    send_payment_reminder, customer_statement, about_view, clear_reminders,
    CustomerViewSet, ProductViewSet, InvoiceViewSet, TransactionViewSet,
    quick_customer_add
)
from .payments import initiate_razorpay_payment, verify_razorpay_payment # Razorpay API: https://razorpay.com/docs/api/
# from .api_views import CustomerViewSet, ProductViewSet, InvoiceViewSet, TransactionViewSet

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'products', ProductViewSet)
router.register(r'invoices', InvoiceViewSet)
router.register(r'transactions', TransactionViewSet)

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('about/', about_view, name='about'),
    
    # Invoices
    path('invoices/', InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/new/', InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:pk>/', InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:pk>/edit/', InvoiceUpdateView.as_view(), name='invoice_edit'),
    path('invoices/<int:pk>/pdf/', generate_pdf, name='invoice_pdf'),
    path('invoices/<int:pk>/email/', email_invoice, name='invoice_email'),
    path('invoices/<int:pk>/pay/', record_payment, name='record_payment'),
    path('invoices/<int:pk>/feedback/', submit_invoice_feedback, name='submit_invoice_feedback'),
    path('invoices/<int:pk>/razorpay/initiate/', initiate_razorpay_payment, name='razorpay_initiate'),
    path('invoices/<int:pk>/razorpay/verify/', verify_razorpay_payment, name='razorpay_verify'),
    path('invoices/<int:pk>/delete/', invoice_delete, name='invoice_delete'),
    path('invoices/reminders/clear/', clear_reminders, name='clear_reminders'),

    # Customers
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('customers/new/', CustomerCreateView.as_view(), name='customer_create'),
    path('customers/quick-add/', quick_customer_add, name='quick_customer_add'),
    path('customers/<int:pk>/edit/', CustomerUpdateView.as_view(), name='customer_edit'),
    path('customers/<int:pk>/delete/', customer_delete, name='customer_delete'),
    
    # Products
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/new/', ProductCreateView.as_view(), name='product_create'),
    path('products/remove-all/', remove_all_products, name='product_remove_all'),
    path('products/<int:pk>/edit/', ProductUpdateView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', product_delete, name='product_delete'),
    
    # Expenses
    path('expenses/', ExpenseListView.as_view(), name='expense_list'),
    path('expenses/new/', ExpenseCreateView.as_view(), name='expense_create'),
    path('expenses/<int:pk>/edit/', ExpenseUpdateView.as_view(), name='expense_edit'),
    path('expenses/<int:pk>/delete/', expense_delete, name='expense_delete'),
    
    # Payment Reminder
    path('invoices/<int:pk>/remind/', send_payment_reminder, name='send_payment_reminder'),
    
    # Customer Statement
    path('customers/<int:pk>/statement/', customer_statement, name='customer_statement'),
    
    # Inventory
    path('inventory/', InventoryDashboardView.as_view(), name='inventory_dashboard'),
    path('inventory/recent-activity/', RecentActivityView.as_view(), name='recent_activity'),
    path('inventory/adjust/<int:pk>/', stock_adjust, name='stock_adjust'),
    path('inventory/add-business-products/', add_all_business_products, name='add_business_products'),
    path('inventory/clear-logs/', clear_inventory_logs, name='clear_inventory_logs'),
    
    # Reports
    path('reports/', ReportsView.as_view(), name='reports'),
    path('reports/pdf/', generate_reports_pdf, name='reports_pdf'),
    
    # Admin Panel
    path('admin-panel/', AdminPanelView.as_view(), name='admin_panel'),
    path('admin-panel/users/', UserManagementView.as_view(), name='user_management'),
    path('admin-panel/users/new/', UserCreateView.as_view(), name='user_create'),
    path('admin-panel/users/<int:pk>/edit/', UserUpdateView.as_view(), name='user_update'),
    path('admin-panel/users/<int:pk>/toggle-status/', user_toggle_status, name='user_toggle_status'),
    path('admin-panel/users/<int:pk>/activity/', UserActivityView.as_view(), name='user_activity'),
    path('admin-panel/users/<int:pk>/delete/', user_delete, name='user_delete'),
    path('admin-panel/users/<int:pk>/send-credentials/', send_user_credentials, name='send_user_credentials'),
    path('admin-panel/settings/', CompanySettingsView.as_view(), name='company_settings'),
    path('admin-panel/settings/reset/', company_settings_reset, name='company_settings_reset'),
    
    # API endpoints
    path('api/', include(router.urls)),
    
    # Client Profile
    path('profile/', ClientProfileView.as_view(), name='client_profile'),
    
    # Authentication (Django auth views with custom template paths)
    path('accounts/login/', auth_views.LoginView.as_view(template_name='authentication/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='authentication/password_reset.html'), name='password_reset_confirm'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('accounts/password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('accounts/password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
]
