# orders/apps.py + models.py (combined)

from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging
import requests
from requests.exceptions import RequestException
import uuid
import sys

# Setup
logger = logging.getLogger(__name__)
User = get_user_model()

# --------------------
# AppConfig Definition
# --------------------

class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'

    def ready(self):
        if 'makemigrations' in sys.argv or 'migrate' in sys.argv or 'test' in sys.argv:
            return

        from .models import Order, OrderItem
        from .signals import order_post_save, order_post_delete, order_item_post_save

        post_save.connect(order_post_save, sender=Order)
        post_delete.connect(order_post_delete, sender=Order)
        post_save.connect(order_item_post_save, sender=OrderItem)

        if not getattr(settings, 'DEBUG', True):
            self._check_service_dependencies()

        logger.info("Order service initialized successfully")

    def _check_service_dependencies(self):
        product_service_url = getattr(settings, "PRODUCT_SERVICE_URL", None)

        if not product_service_url:
            logger.warning("PRODUCT_SERVICE_URL is not set in settings.")
            return

        try:
            response = requests.get(f"{product_service_url}/health/", timeout=2)
            if response.status_code == 200:
                logger.info(f"Product service is available at {product_service_url}")
            else:
                logger.warning(f"Product service returned {response.status_code}. Degraded mode.")
        except RequestException as e:
            logger.warning(f"Could not connect to product service: {str(e)}. Degraded mode.")

# --------------------
# Models
# --------------------

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Product(models.Model):
    external_id = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    image_url = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    last_synced = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @classmethod
    def sync_from_product_service(cls, product_data):
        external_id = product_data.get('id')
        if not external_id:
            logger.error("Cannot sync product without external ID")
            return None

        category_data = product_data.get('category')
        category_name = category_data.get('name') if isinstance(category_data, dict) else category_data or 'Uncategorized'
        category, _ = Category.objects.get_or_create(name=category_name)

        product, created = cls.objects.update_or_create(
            external_id=external_id,
            defaults={
                'name': product_data.get('name', 'Unknown Product'),
                'price': product_data.get('price', 0.00),
                'description': product_data.get('description', ''),
                'category': category,
                'image_url': product_data.get('image_url', ''),
                'is_available': product_data.get('is_available', True),
                'last_synced': timezone.now(),
            }
        )
        action = "Created" if created else "Updated"
        logger.info(f"{action} product {product.name} (ID: {external_id})")
        return product


class Order(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("CONFIRMED", "Confirmed"),
        ("PREPARING", "Preparing"),
        ("READY", "Ready"),
        ("DELIVERED", "Delivered"),
        ("CANCELLED", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='orders')
    customer_name = models.CharField(max_length=100, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    special_requests = models.TextField(blank=True)
    table_number = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    preparing_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    payment_id = models.CharField(max_length=100, blank=True)
    payment_status = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Order {self.id} ({self.status})"

    def recalculate_total(self):
        total = sum(item.product.price * item.quantity for item in self.items.all())
        self.total_price = total
        self.save(update_fields=['total_price'])
        return total

    def update_status(self, new_status):
        if new_status == self.status:
            return False

        old_status = self.status
        self.status = new_status

        timestamp_map = {
            "CONFIRMED": "confirmed_at",
            "PREPARING": "preparing_at",
            "READY": "ready_at",
            "DELIVERED": "delivered_at",
            "CANCELLED": "cancelled_at",
        }

        ts_field = timestamp_map.get(new_status)
        if ts_field:
            setattr(self, ts_field, timezone.now())

        self.save()
        logger.info(f"Order {self.id} status changed: {old_status} -> {new_status}")
        return True

    def get_preparation_time(self):
        if self.confirmed_at and self.ready_at:
            delta = self.ready_at - self.confirmed_at
            return int(delta.total_seconds() / 60)
        return None

    def get_delivery_time(self):
        if self.ready_at and self.delivered_at:
            delta = self.delivered_at - self.ready_at
            return int(delta.total_seconds() / 60)
        return None

    def get_total_time(self):
        if self.confirmed_at and self.delivered_at:
            delta = self.delivered_at - self.confirmed_at
            return int(delta.total_seconds() / 60)
        return None

    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    special_instructions = models.CharField(max_length=255, blank=True)
    is_prepared = models.BooleanField(default=False)
    preparation_started_at = models.DateTimeField(null=True, blank=True)
    preparation_completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if is_new and not self.unit_price:
            self.unit_price = self.product.price

        super().save(*args, **kwargs)

        if is_new or 'quantity' in kwargs.get('update_fields', []):
            self.order.recalculate_total()

    def get_subtotal(self):
        return self.quantity * self.unit_price

    def mark_prepared(self):
        if not self.is_prepared:
            self.is_prepared = True
            self.preparation_completed_at = timezone.now()
            self.save(update_fields=['is_prepared', 'preparation_completed_at'])
            return True
        return False

    class Meta:
        unique_together = ('order', 'product')
