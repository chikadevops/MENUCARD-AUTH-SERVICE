from rest_framework import serializers
from django.utils import timezone
from .models import Category, Product, Order, OrderItem

class CategorySerializer(serializers.ModelSerializer):
    """Serializer for product categories."""
    product_count = serializers.IntegerField(read_only=True, required=False)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'product_count']

class ProductSerializer(serializers.ModelSerializer):
    """Serializer for menu products with availability information."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'external_id', 'name', 'price', 'description', 
            'category', 'category_name', 'image_url', 'is_available', 
            'last_synced'
        ]
        read_only_fields = ['external_id', 'last_synced']
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be a positive value.")
        return value

class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for individual items within an order."""
    product_details = ProductSerializer(source='product', read_only=True)
    subtotal = serializers.DecimalField(
        max_digits=10, decimal_places=2, 
        read_only=True, source='get_subtotal'
    )
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_details', 'quantity', 
            'unit_price', 'special_instructions', 'subtotal',
            'is_prepared', 'preparation_started_at', 'preparation_completed_at'
        ]
        read_only_fields = ['id', 'unit_price', 'is_prepared', 
                           'preparation_started_at', 'preparation_completed_at']
    
    def validate_quantity(self, value):
        """Ensure quantity is positive."""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero")
        return value
    
    def validate_product(self, value):
        if hasattr(value, 'is_available') and not value.is_available:
            raise serializers.ValidationError(f"Product '{value.name}' is currently unavailable.")
        return value

class OrderSerializer(serializers.ModelSerializer):
    """Serializer for customer orders with nested items."""
    items = OrderItemSerializer(many=True)
    preparation_time = serializers.IntegerField(source='get_preparation_time', read_only=True)
    delivery_time = serializers.IntegerField(source='get_delivery_time', read_only=True)
    total_time = serializers.IntegerField(source='get_total_time', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'customer_name', 'customer_email', 'customer_phone',
            'items', 'status', 'total_price', 'table_number', 'special_requests',
            'created_at', 'updated_at', 'confirmed_at', 'preparing_at', 
            'ready_at', 'delivered_at', 'cancelled_at',
            'payment_id', 'payment_status', 'payment_method', 'is_takeaway',
            'preparation_time', 'delivery_time', 'total_time'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'confirmed_at', 'preparing_at', 
            'ready_at', 'delivered_at', 'cancelled_at', 'total_price',
            'payment_id', 'payment_status'
        ]

    def create(self, validated_data):
        """Create order with nested items and calculate total price."""
        items_data = validated_data.pop('items')
        
        # Create the order
        order = Order.objects.create(**validated_data)
        
        # Create order items
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            
            # Create the order item with unit price
            OrderItem.objects.create(
                order=order,
                unit_price=product.price,
                **item_data
            )
        
        # Recalculate total (will be done automatically by OrderItem.save)
        order.recalculate_total()
        
        return order

    def update(self, instance, validated_data):
        """Update order with support for adding, modifying, and removing items."""
        items_data = validated_data.pop('items', None)
        
        # Update order fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update status with timestamp tracking
        if 'status' in validated_data and validated_data['status'] != instance.status:
            instance.update_status(validated_data['status'])
        else:
            instance.save()
        
        # Handle items if provided
        if items_data is not None:
            # Track current items for potential removal
            current_items = {item.id: item for item in instance.items.all()}
            updated_item_ids = []
            
            # Process provided items
            for item_data in items_data:
                item_id = item_data.get('id')
                
                if item_id and item_id in current_items:
                    # Update existing item
                    item = current_items[item_id]
                    item.product = item_data.get('product', item.product)
                    item.quantity = item_data.get('quantity', item.quantity)
                    item.special_instructions = item_data.get('special_instructions', item.special_instructions)
                    item.save()
                    updated_item_ids.append(item_id)
                else:
                    # Create new item with current product price
                    product = item_data['product']
                    new_item = OrderItem.objects.create(
                        order=instance, 
                        unit_price=product.price,
                        **item_data
                    )
                    updated_item_ids.append(new_item.id)
            
            # Remove items not in the update
            for item_id, item in current_items.items():
                if item_id not in updated_item_ids:
                    item.delete()
            
            # Recalculate total price
            instance.recalculate_total()
        
        return instance

    def validate(self, data):
        """Validate order data including status and items."""
        # Validate status
        status_options = ['PENDING', 'CONFIRMED', 'PREPARING', 'READY', 'DELIVERED', 'CANCELLED']
        if 'status' in data and data.get('status') not in status_options:
            raise serializers.ValidationError({
                "status": f"Invalid status. Must be one of: {', '.join(status_options)}"
            })
        
        # Validate items exist
        if 'items' in data and not data.get('items'):
            raise serializers.ValidationError({
                "items": "Order must have at least one item"
            })
        
        # Validate product availability
        if 'items' in data:
            for item_data in data['items']:
                product = item_data['product']
                if hasattr(product, 'is_available') and not product.is_available:
                    raise serializers.ValidationError({
                        "items": f"Product '{product.name}' is currently unavailable"
                    })
        
        return data
    
class OrderStatusSerializer(serializers.ModelSerializer):
    """Serializer for updating only the order status."""
    status_notes = serializers.CharField(required=False, allow_blank=True, write_only=True)
    estimated_completion_time = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = Order
        fields = ['status', 'status_notes', 'estimated_completion_time']
        extra_kwargs = {
            'status': {
                'required': True,
                'help_text': 'New status for the order'
            }
        }

    def validate_status(self, value):
        """Validate that the provided status is among the allowed values."""
        allowed = ['PENDING', 'CONFIRMED', 'PREPARING', 'READY', 'DELIVERED', 'CANCELLED']
        if value not in allowed:
            raise serializers.ValidationError(
                f"Invalid status. Choose from: {', '.join(allowed)}"
            )
        return value
        
    def update(self, instance, validated_data):
        """Update order status with timestamp tracking."""
        status = validated_data.pop('status', None)
        
        if status and status != instance.status:
            instance.update_status(status)
            
        return instance

class KitchenOrderSerializer(serializers.ModelSerializer):
    """Simplified serializer for kitchen display systems."""
    items = serializers.SerializerMethodField()
    time_elapsed = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'status', 'table_number', 'customer_name',
            'items', 'special_requests', 'is_takeaway',
            'created_at', 'confirmed_at', 'time_elapsed'
        ]
    
    def get_items(self, obj):
        """Get simplified item representation for kitchen."""
        return [{
            'id': item.id,
            'name': item.product.name,
            'quantity': item.quantity,
            'instructions': item.special_instructions,
            'is_prepared': item.is_prepared,
            'category': item.product.category.name if item.product.category else 'Uncategorized'
        } for item in obj.items.all()]
    
    def get_time_elapsed(self, obj):
        """Get minutes elapsed since order confirmation."""
        if not obj.confirmed_at:
            return 0
        
        elapsed = timezone.now() - obj.confirmed_at
        return int(elapsed.total_seconds() // 60)

class OrderEventSerializer(serializers.ModelSerializer):
    """Serializer for publishing order events to other services."""
    order_id = serializers.UUIDField(source='id')
    user_id = serializers.IntegerField(source='user.id', required=False)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'order_id', 'user_id', 'status', 'total_price',
            'created_at', 'updated_at', 'item_count',
            'table_number', 'is_takeaway', 'payment_status'
        ]
    
    def get_item_count(self, obj):
        return obj.items.count()
    
    