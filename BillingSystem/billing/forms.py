"""
Django forms for billing-related models, including custom widgets
and validation for Customers, Products, and Expenses.
"""
from django import forms
from django.contrib.auth.models import User
from .models import Customer

class CustomerForm(forms.ModelForm):
    assigned_user = forms.ModelChoiceField(
        queryset=User.objects.filter(role__role='client'),
        required=False,
        label="Assign Client Login",
        widget=forms.Select(attrs={'class': 'w-full border border-gray-300 px-3 py-2'}),
        empty_label="-- Select Client User --",
        help_text="Select a client user to give them access to this customer's portal."
    )

    # Make phone optional — only Name and Email are required
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2'})
    )

    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone', 'company_name', 'contact_person', 'company_type', 'address1', 'address2', 'landmark', 'pincode', 'city', 'state', 'country', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2'}),
            'email': forms.EmailInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2'}),
            'company_name': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2'}),
            'contact_person': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2'}),
            'company_type': forms.Select(attrs={'class': 'w-full border border-gray-300 px-3 py-2'}, choices=[
                ('', '-- Select Company Type --'),
                ('Proprietorship', 'Proprietorship'),
                ('Partnership', 'Partnership'),
                ('LLP', 'LLP (Limited Liability Partnership)'),
                ('Private Limited', 'Private Limited'),
                ('Public Limited', 'Public Limited'),
                ('OPC', 'OPC (One Person Company)'),
            ]),
            'address1': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2', 'placeholder': 'Street address, building name'}),
            'address2': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2', 'placeholder': 'Apartment, suite, unit, etc.'}),
            'landmark': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2'}),
            'pincode': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2'}),
            'city': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2'}),
            'state': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2'}),
            'country': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2'}),
            'address': forms.Textarea(attrs={'class': 'w-full border border-gray-300 px-3 py-2', 'rows': 3}),
        }

from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'hsn_code', 'gst_rate', 'discount', 'category', 'low_stock_threshold']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2'}),
            'description': forms.Textarea(attrs={'class': 'w-full border border-gray-300 px-3 py-2', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2', 'min': '0', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2', 'min': '0'}),
            'hsn_code': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2'}),
            'gst_rate': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2', 'min': '0', 'step': '0.01', 'id': 'id_gst_rate'}),
            'discount': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2', 'min': '0', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'w-full border border-gray-300 px-3 py-2'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2', 'min': '0'}),
        }

from .models import Expense

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'amount', 'category', 'description', 'date', 'reference']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2 rounded-lg'}),
            'amount': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2 rounded-lg', 'min': '0', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'w-full border border-gray-300 px-3 py-2 rounded-lg'}),
            'description': forms.Textarea(attrs={'class': 'w-full border border-gray-300 px-3 py-2 rounded-lg', 'rows': 3}),
            'date': forms.DateInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2 rounded-lg', 'type': 'date'}),
            'reference': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2 rounded-lg'}),
        }

from django.contrib.auth.models import User
from .models import UserProfile

class ClientUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2 rounded'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2 rounded'}),
            'email': forms.EmailInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2 rounded'}),
        }

class ClientProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'phone', 'company_name', 'company_type',
            'address1', 'address2', 'landmark', 'city', 'state', 'pincode', 'country'
        ]
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2 rounded'}),
            'company_name': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2 rounded'}),
            'company_type': forms.Select(attrs={'class': 'w-full border border-gray-300 px-3 py-2 rounded'}, choices=[
                ('', '-- Select Company Type --'),
                ('Proprietorship', 'Proprietorship'),
                ('Partnership', 'Partnership'),
                ('LLP', 'LLP (Limited Liability Partnership)'),
                ('Private Limited', 'Private Limited'),
                ('Public Limited', 'Public Limited'),
                ('OPC', 'OPC (One Person Company)'),
            ]),
            'address1': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2 rounded'}),
            'address2': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2 rounded'}),
            'landmark': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2 rounded'}),
            'city': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2 rounded'}),
            'state': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2 rounded'}),
            'pincode': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2 rounded'}),
            'country': forms.TextInput(attrs={'class': 'w-full border border-gray-300 px-3 py-2 rounded'}),
        }

