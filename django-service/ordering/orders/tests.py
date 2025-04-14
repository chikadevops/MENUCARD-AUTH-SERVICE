# orders/tests.py
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from .models import Category, Product, Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer

User = get_user_model()

# =============== Base Test Case ===============
class OrderingServiceTestCase(APITestCase):
    """Base test case for ordering service tests."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpassword',
            is_staff=True
        )
        
        # Create test categories
        self.category1 = Category.objects.create(name='Main Course')
        self.category2 = Category.objects.create(name='Dessert')
        
        # Create test products
        self.product1 = Product.objects.create(
            external_id='ext-1',
            name='Burger',
            price=9.99,
            description='Delicious burger',
            category=self.category1,
            is_available=True
        )
        
        self.product2 = Product.objects.create(
            external_id='ext-2',
            name='Pizza',
            price=12.99,
            description='Tasty pizza',
            category=self.category1,
            is_available=True
        )
        
        self.product3 = Product.objects.create(
            external_id='ext-3',
            name='Ice Cream',
            price=5.99,
            description='Sweet ice cream',
            category=self.category2,
            is_available=True
        )
        
        # Create a test order
        self.order = Order.objects.create(
            user=self.user,
            status='PENDING',
            customer_name='Test Customer',
            table_number=5
        )
        
        # Add items to the order
        self.order_item1 = OrderItem.objects.create(
            order=self.order,
            product=self.product1,
            quantity=2,
            unit_price=self.product1.price
        )
        
        self.order_item2 = OrderItem.objects.create(
            order=self.order,
            product=self.product3,
            quantity=1,
            unit_price=self.product3.price
        )
        
        # Update order total
        self.order.recalculate_total()
        
        # Set up authentication
        self.client.force_authenticate(user=self.user)
        
    def authenticate_staff(self):
        """Switch to staff user authentication."""
        self.client.force_authenticate(user=self.staff_user)

# =============== Model Tests ===============
class OrderModelTest(TestCase):
    """Test the Order model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        self.category = Category.objects.create(name='Main Course')
        
        self.product1 = Product.objects.create(
            external_id='ext-1',
            name='Burger',
            price=9.99,
            category=self.category,
            is_available=True
        )
        
        self.product2 = Product.objects.create(
            external_id='ext-2',
            name='Fries',
            price=4.99,
            category=self.category,
            is_available=True
        )
        
        self.order = Order.objects.create(
            user=self.user,
            status='PENDING',
            customer_name='Test Customer'
        )
        
    def test_recalculate_total(self):
        """Test that total price is calculated correctly."""
        # Add items to order
        OrderItem.objects.create(
            order=self.order,
            product=self.product1,
            quantity=2,
            unit_price=self.product1.price
        )
        
        OrderItem.objects.create(
            order=self.order,
            product=self.product2,
            quantity=1,
            unit_price=self.product2.price
        )
        
        # Recalculate total
        self.order.recalculate_total()
        
        # Expected total: (9.99 * 2) + (4.99 * 1) = 24.97
        expected_total = (self.product1.price * 2) + (self.product2.price * 1)
        self.assertEqual(self.order.total_price, expected_total)
    
    def test_update_status(self):
        """Test status updates with timestamps."""
        # Update to CONFIRMED
        self.order.update_status('CONFIRMED')
        self.assertEqual(self.order.status, 'CONFIRMED')
        self.assertIsNotNone(self.order.confirmed_at)
        
        # Update to PREPARING
        self.order.update_status('PREPARING')
        self.assertEqual(self.order.status, 'PREPARING')
        self.assertIsNotNone(self.order.preparing_at)

# =============== Serializer Tests ===============
class OrderSerializerTest(TestCase):
    """Test the Order serializer."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        self.category = Category.objects.create(name='Main Course')
        
        self.product1 = Product.objects.create(
            external_id='ext-1',
            name='Burger',
            price=9.99,
            category=self.category,
            is_available=True
        )
        
        self.product2 = Product.objects.create(
            external_id='ext-2',
            name='Fries',
            price=4.99,
            category=self.category,
            is_available=True
        )
    
    def test_order_serializer_create(self):
        """Test creating an order with the serializer."""
        data = {
            'user': self.user.id,
            'customer_name': 'John Doe',
            'table_number': 3,
            'status': 'PENDING',
            'items': [
                {
                    'product': self.product1.id,
                    'quantity': 2,
                    'special_instructions': 'No onions'
                },
                {
                    'product': self.product2.id,
                    'quantity': 1
                }
            ]
        }
        
        serializer = OrderSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        order = serializer.save()
        
        # Check order was created correctly
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.customer_name, 'John Doe')
        self.assertEqual(order.items.count(), 2)

# =============== API View Tests ===============
class ProductViewSetTest(OrderingServiceTestCase):
    """Test the ProductViewSet."""
    
    def test_list_products(self):
        """Test listing all products."""
        url = reverse('product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
    
    def test_filter_products_by_category(self):
        """Test filtering products by category."""
        url = reverse('product-list')
        response = self.client.get(url, {'category': 'Main Course'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

class OrderViewSetTest(OrderingServiceTestCase):
    """Test the OrderViewSet."""
    
    @patch('requests.get')
    def test_create_order(self, mock_get):
        """Test creating an order."""
        # Mock the product service response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            str(self.product1.id): {'available': True},
            str(self.product2.id): {'available': True}
        }
        mock_get.return_value = mock_response
        
        url = reverse('order-list')
        data = {
            'customer_name': 'New Customer',
            'table_number': 7,
            'items': [
                {
                    'product': self.product1.id,
                    'quantity': 1
                },
                {
                    'product': self.product2.id,
                    'quantity': 2
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check order was created
        order_id = response.data['id']
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.customer_name, 'New Customer')
        self.assertEqual(order.items.count(), 2)

# =============== Health Check Test ===============
class HealthCheckTest(TestCase):
    """Test the health check endpoint."""
    
    @patch('requests.get')
    def test_health_check(self, mock_get):
        """Test health check endpoint."""
        # Mock the product service health check
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        url = reverse('health-check')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'healthy')


