from django.shortcuts import render


# Create your views here.
from rest_framework import generics, status, filters, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.db.models import Prefetch, Count, Sum, Q
from django.utils import timezone
from django.core.cache import cache
from .models import Product, Order, OrderItem, Category
from .serializers import (
    ProductSerializer, OrderSerializer, OrderStatusSerializer,
    CategorySerializer, OrderItemSerializer, KitchenOrderSerializer
)
import requests
from django.conf import settings
from requests.exceptions import RequestException
from django.http import JsonResponse
from django.db import connection
import logging

# Set up logging
logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """Public API root with information about available endpoints."""
    return Response({
        "service": "Digital Menu Card API - Ordering Service",
        "version": "1.0.0",
        "public_endpoints": {
            "products": "/api/products/",
            "categories": "/api/categories/",
            "featured_products": "/api/products/featured/",
            "products_by_category": "/api/products/by_category/",
        },
        "authenticated_endpoints": {
            "orders": "/api/orders/",
            "order_items": "/api/order-items/",
        },
        "documentation": "/api/docs/",  # If you add API docs
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint for orchestration systems."""
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "up"
    except Exception:
        db_status = "down"
    
    # Check dependent services if needed
    dependencies = {
        "database": db_status,
    }
    
    # Check product service
    try:
        response = requests.get(
            f"{settings.PRODUCT_SERVICE_URL}/health/",
            timeout=1
        )
        product_service_status = "up" if response.status_code == 200 else "down"
    except Exception:
        product_service_status = "down"
    
    dependencies["product_service"] = product_service_status
    
    status = "healthy" if all(v == "up" for v in dependencies.values()) else "degraded"
    
    return JsonResponse({
        "status": status,
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "dependencies": dependencies,
        "timestamp": timezone.now().isoformat()
    })

# Add to the top of your file
class CircuitBreaker:
    """Simple circuit breaker implementation."""
    def __init__(self, name, max_failures=3, reset_timeout=60):
        self.name = name
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self.last_failure_time = None
    
    def execute(self, func, *args, **kwargs):
        """Execute function with circuit breaker pattern."""
        import time
        
        if self.state == "OPEN":
            # Check if timeout has elapsed
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.reset_timeout:
                self.state = "HALF-OPEN"
                logger.info(f"Circuit {self.name} changed from OPEN to HALF-OPEN")
            else:
                raise Exception(f"Circuit {self.name} is OPEN")
        
        try:
            result = func(*args, **kwargs)
            
            # If successful and in HALF-OPEN, reset circuit
            if self.state == "HALF-OPEN":
                self.reset()
                
            return result
            
        except Exception as e:
            self.record_failure()
            raise e
    
    def record_failure(self):
        """Record a failure and potentially open the circuit."""
        import time
        
        self.failures += 1
        self.last_failure_time = time.time()
        
        if self.failures >= self.max_failures:
            self.state = "OPEN"
            logger.warning(f"Circuit {self.name} changed to OPEN after {self.failures} failures")
    
    def reset(self):
        """Reset the circuit breaker to closed state."""
        self.failures = 0
        self.state = "CLOSED"
        self.last_failure_time = None
        logger.info(f"Circuit {self.name} reset to CLOSED")

# Create circuit breaker instance
product_service_cb = CircuitBreaker("product-service")

# Then in your create method:
def create(self, request, *args, **kwargs):
    """Create order with product validation from catalog service."""
    # Validate products exist in catalog service
    try:
        product_ids = [item['product'] for item in request.data.get('items', [])]
        
        # Define function to call product service
        def call_product_service():
            response = requests.get(
                f"{settings.PRODUCT_SERVICE_URL}/api/products/validate/",
                params={'ids': ','.join(map(str, product_ids))},
                timeout=3
            )
            if response.status_code != 200:
                raise RequestException(f"Product service returned {response.status_code}")
            return response
        
        # Use circuit breaker
        try:
            response = product_service_cb.execute(call_product_service)
            
            valid_products = response.json()
            
            # Check if all products are available
            for product_id in product_ids:
                if str(product_id) not in valid_products or not valid_products[str(product_id)]['available']:
                    return Response(
                        {"detail": f"Product {product_id} is unavailable"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
        except Exception as e:
            logger.warning(f"Product validation failed: {str(e)}")
            # Continue with degraded functionality
            
    except Exception as e:
        logger.error(f"Error during product validation: {str(e)}")
        # Continue with order creation
        
    return super().create(request, *args, **kwargs)


# Product Views
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for products with filtering, searching and caching.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['name', 'price', 'category']
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Optimize queries and implement caching."""
        # Cache key based on query parameters
        cache_key = f"products:{self.request.query_params}"
        queryset = cache.get(cache_key)
        
        if not queryset:
            queryset = Product.objects.select_related('category').all()
            
            # Filter by category if provided
            category = self.request.query_params.get('category')
            if category:
                queryset = queryset.filter(category__name__iexact=category)
            
            # Filter by availability
            available = self.request.query_params.get('available')
            if available and available.lower() == 'true':
                queryset = queryset.filter(is_available=True)
            
            # Filter by price range
            min_price = self.request.query_params.get('min_price')
            max_price = self.request.query_params.get('max_price')
            if min_price:
                queryset = queryset.filter(price__gte=float(min_price))
            if max_price:
                queryset = queryset.filter(price__lte=float(max_price))
                
            # Cache for 10 minutes
            cache.set(cache_key, queryset, 60 * 10)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Return featured products."""
        featured = self.get_queryset().filter(is_featured=True)[:8]
        serializer = self.get_serializer(featured, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Group products by category for menu display."""
        categories = Category.objects.prefetch_related(
            Prefetch('products', queryset=Product.objects.filter(is_available=True))
        )
        
        result = {}
        for category in categories:
            serializer = ProductSerializer(category.products.all(), many=True)
            result[category.name] = serializer.data
            
        return Response(result)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def sync_products(self, request):
        """
        Sync products from the product service.
        Admin-only endpoint.
        """
        try:
            # Call product service to get all products
            response = requests.get(
                f"{settings.PRODUCT_SERVICE_URL}/api/products/",
                params={'limit': 1000},  # Adjust based on your needs
                timeout=10  # Longer timeout for bulk operation
            )
            
            if response.status_code != 200:
                return Response(
                    {"detail": "Unable to fetch products from product service"}, 
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
                
            products_data = response.json()
            
            # Process each product
            synced_count = 0
            for product_data in products_data.get('results', []):
                Product.sync_from_product_service(product_data)
                synced_count += 1
                
            return Response({
                "detail": f"Successfully synced {synced_count} products",
                "count": synced_count
            })
            
        except RequestException as e:
            logger.error(f"Product service unavailable during sync: {str(e)}")
            return Response(
                {"detail": "Product service unavailable"}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

# Category Views
class CategoryList(generics.ListAPIView):
    """List all product categories."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Add product counts to categories."""
        return Category.objects.annotate(
            product_count=Count('products'),
            available_products=Count('products', filter=Q(products__is_available=True))
        )

# Order Views

class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for orders with optimized queries and additional actions.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Optimize order queries with prefetch_related."""
        user = self.request.user
        
        # Staff can see all orders
        if user.is_staff:
            queryset = Order.objects.all()
        else:
            queryset = Order.objects.filter(user=user)
            
        # Always prefetch related items and products for performance
        return queryset.prefetch_related(
            Prefetch('items', queryset=OrderItem.objects.select_related('product'))
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set user automatically on create."""
        serializer.save(user=self.request.user)
    
    # ADD THIS NEW METHOD for microservice communication
    def create(self, request, *args, **kwargs):
        """Create order with product validation and input checks."""
        items = request.data.get('items', [])
        
        if not items:
            return Response({"detail": "Order must contain at least one item."}, status=status.HTTP_400_BAD_REQUEST)

        # Input validation before external call
        product_ids = []
        for item in items:
            if 'product' not in item or 'quantity' not in item:
                return Response({"detail": "Each item must include 'product' and 'quantity'."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                qty = int(item['quantity'])
                if qty <= 0:
                    raise ValueError
            except ValueError:
                return Response({"detail": f"Invalid quantity for product {item.get('product')}"}, status=status.HTTP_400_BAD_REQUEST)
            product_ids.append(item['product'])

        # Remote catalog service validation
        try:
            response = requests.get(
                f"{settings.PRODUCT_SERVICE_URL}/api/products/validate/",
                params={'ids': ','.join(map(str, product_ids))},
                timeout=3
            )

            if response.status_code != 200:
                return Response({"detail": "Unable to validate products"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            valid_products = response.json()

            for product_id in product_ids:
                if str(product_id) not in valid_products or not valid_products[str(product_id)]['available']:
                    return Response({"detail": f"Product {product_id} is unavailable"}, status=status.HTTP_400_BAD_REQUEST)

        except RequestException as e:
            logger.error(f"Product service unavailable: {str(e)}")
            logger.warning("Proceeding without remote product validation")

        # Proceed with order creation
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """
        Update order status only - optimized for kitchen/staff use.
        Uses the simplified OrderStatusSerializer.
        """
        order = self.get_object()
        serializer = OrderStatusSerializer(order, data=request.data, partial=True)
        
        if serializer.is_valid():
            # Track status change time
            new_status = serializer.validated_data.get('status')
            if new_status and new_status != order.status:
                # Set timestamp based on status
                if new_status == 'CONFIRMED':
                    order.confirmed_at = timezone.now()
                elif new_status == 'PREPARING':
                    order.preparing_at = timezone.now()
                elif new_status == 'READY':
                    order.ready_at = timezone.now()
                elif new_status == 'DELIVERED':
                    order.delivered_at = timezone.now()
            
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active orders (not delivered or cancelled)."""
        active_orders = self.get_queryset().exclude(
            status__in=['DELIVERED', 'CANCELLED']
        )
        serializer = self.get_serializer(active_orders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def kitchen_view(self, request):
        """
        Specialized endpoint for kitchen display system.
        Requires staff permissions.
        """
        if not request.user.is_staff:
            return Response(
                {"detail": "Not authorized"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Get orders that need preparation
        preparing_orders = Order.objects.filter(
            status__in=['CONFIRMED', 'PREPARING']
        ).prefetch_related(
            Prefetch('items', queryset=OrderItem.objects.select_related('product'))
        ).order_by('created_at')
        
        # Use the specialized KitchenOrderSerializer
        serializer = KitchenOrderSerializer(preparing_orders, many=True)
        return Response(serializer.data)
        
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get order statistics (admin only).
        """
        if not request.user.is_staff:
            return Response(
                {"detail": "Not authorized"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Get today's date
        today = timezone.now().date()
        
        # Calculate statistics
        stats = {
            'today_orders': Order.objects.filter(created_at__date=today).count(),
            'today_revenue': Order.objects.filter(
                created_at__date=today, 
                status='DELIVERED'
            ).aggregate(total=Sum('total_price'))['total'] or 0,
            'pending_orders': Order.objects.filter(status='PENDING').count(),
            'preparing_orders': Order.objects.filter(status='PREPARING').count(),
            'ready_orders': Order.objects.filter(status='READY').count(),
            'avg_preparation_time': 0,  # Calculate from timestamps
        }
        
        # Calculate average preparation time
        completed_orders = Order.objects.filter(
            confirmed_at__isnull=False,
            ready_at__isnull=False
        )
        
        if completed_orders.exists():
            total_minutes = 0
            count = 0
            
            for order in completed_orders:
                prep_time = (order.ready_at - order.confirmed_at).total_seconds() // 60
                total_minutes += prep_time
                count += 1
                
            stats['avg_preparation_time'] = round(total_minutes / count, 1)
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get user's order history with pagination."""
        user = request.user
        
        # Get completed orders for this user
        completed_orders = Order.objects.filter(
            user=user,
            status__in=['DELIVERED', 'CANCELLED']
        ).prefetch_related(
            Prefetch('items', queryset=OrderItem.objects.select_related('product'))
        ).order_by('-created_at')
        
        # Apply pagination
        page = self.paginate_queryset(completed_orders)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(completed_orders, many=True)
        return Response(serializer.data)

# Order Item Views (for individual item updates)
class OrderItemUpdate(generics.UpdateAPIView):
    """
    Update individual order items (e.g., mark as prepared).
    Useful for kitchen staff to mark items as they're completed.
    """
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_update(self, serializer):
        """Track when items are marked as prepared."""
        if 'is_prepared' in self.request.data and self.request.data['is_prepared']:
            serializer.save(preparation_completed_at=timezone.now())
        else:
            serializer.save()
            
            