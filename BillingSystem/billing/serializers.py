"""
REST Framework serializers for Billing models.
Handles complex data validation, nested object creation, and stock management.
"""
from decimal import Decimal
from rest_framework import serializers
from .models import Customer, Product, Invoice, InvoiceItem, Transaction, Company

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0'))
    stock = serializers.IntegerField(min_value=0)
    gst_rate = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal('0'))

    class Meta:
        model = Product
        fields = '__all__'

class InvoiceItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')

    class Meta:
        model = InvoiceItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price']

class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True) # Remove read_only=True to allow write
    customer_name = serializers.ReadOnlyField(source='customer.name')

    class Meta:
        model = Invoice
        fields = ['id', 'customer', 'customer_name', 'date', 'total_amount', 'qr_code', 'is_paid', 
                  'dispatch_through', 'due_date', 'payment_terms', 'payment_note', 'terms_and_conditions',
                  'document_note', 'bank_details', 'items']
    
    def create(self, validated_data):
        from django.db import transaction
        from collections import defaultdict
        
        items_data = validated_data.pop('items')
        
        # 1. Aggregate quantities per product
        aggregate_quantities = defaultdict(int)
        for item_data in items_data:
            product = item_data['product']
            aggregate_quantities[product.id] += item_data['quantity']
        
        # 2. Process in transaction to ensure consistency
        with transaction.atomic():
            # Auto-populate Terms from Company Settings
            company = Company.objects.first()
            if company and not validated_data.get('terms_and_conditions'):
                validated_data['terms_and_conditions'] = company.terms_and_conditions
                
            invoice = Invoice.objects.create(**validated_data)
            total = 0 # Total including Tax
            
            # Fetch all involved products with locking to prevent race conditions
            product_ids = aggregate_quantities.keys()
            products_dict = {p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids)}
            
            # 3. Validate aggregate quantities against current stock
            for p_id, total_qty in aggregate_quantities.items():
                product = products_dict.get(p_id)
                if not product:
                    raise serializers.ValidationError(f"Product with ID {p_id} not found.")
                
                if product.stock <= 0:
                    raise serializers.ValidationError(
                        f"Cannot add '{product.name}' to invoice - product is OUT OF STOCK."
                    )
                
                if product.stock < total_qty:
                    raise serializers.ValidationError(
                        f"Insufficient total stock for '{product.name}'. "
                        f"Available: {product.stock}, Requested Total: {total_qty} across all lines."
                    )

            # 4. Create items (Deduction is handled by signal in signals.py)
            for item_data in items_data:
                # Create Item - This triggers adjust_stock_on_save signal in signals.py
                item = InvoiceItem.objects.create(invoice=invoice, **item_data)
                
                # Accumulate Total (Price * Qty + GST)
                taxable = item.price * item.quantity
                total += taxable + item.gst_amount
            
            invoice.total_amount = total
            invoice.save()
            return invoice

    def update(self, instance, validated_data):
        from django.db import transaction
        from collections import defaultdict
        
        items_data = validated_data.pop('items')
        
        # 1. Calculate Net Stock Change Required
        new_quantities = defaultdict(int)
        for item in items_data:
            new_quantities[item['product'].id] += item['quantity']
            
        old_quantities = defaultdict(int)
        for item in instance.items.all():
            old_quantities[item.product.id] += item.quantity
            
        # 2. Validate Stock Availability
        with transaction.atomic():
            # Lock products to prevent race conditions during validation
            all_product_ids = set(new_quantities.keys()) | set(old_quantities.keys())
            products_dict = {p.id: p for p in Product.objects.select_for_update().filter(id__in=all_product_ids)}
            
            for p_id, new_qty in new_quantities.items():
                old_qty = old_quantities.get(p_id, 0)
                net_change = new_qty - old_qty
                
                if net_change > 0:
                    product = products_dict.get(p_id)
                    if not product:
                        raise serializers.ValidationError(f"Product with ID {p_id} not found.")
                    
                    if product.stock < net_change:
                         raise serializers.ValidationError(
                            f"Insufficient stock for '{product.name}'. "
                            f"Available: {product.stock}, "
                            f"Previously Ordered: {old_qty}, "
                            f"New Total: {new_qty}. "
                            f"Shortfall: {net_change - product.stock}"
                        )

            # 3. Apply Updates
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            
            # Delete old items (Triggers signal -> Restores Stock)
            instance.items.all().delete()
            
            # Create new items (Triggers signal -> Deducts Stock)
            total = 0
            for item_data in items_data:
                item = InvoiceItem.objects.create(invoice=instance, **item_data)
                taxable = item.price * item.quantity
                total += taxable + item.gst_amount
            
            instance.total_amount = total
            instance.save()
            return instance

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
