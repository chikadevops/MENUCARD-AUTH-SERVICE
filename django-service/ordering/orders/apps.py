from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete
from django.conf import settings
import logging
import requests
from requests.exceptions import RequestException
import sys

logger = logging.getLogger(__name__)

class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'
    
    def ready(self):
        """
        Initialize application components when Django starts.
        This is where we set up signal handlers, check service dependencies,
        and initialize any required components.
        """
        # Avoid running this in migrations or test environments
        if 'makemigrations' in sys.argv or 'migrate' in sys.argv or 'test' in sys.argv:
            return

        # Import models and signals locally to avoid circular imports
        from .models import Order, OrderItem
        from .signals import order_post_save, order_post_delete, order_item_post_save

        # Connect signal handlers
        post_save.connect(order_post_save, sender=Order)
        post_delete.connect(order_post_delete, sender=Order)
        post_save.connect(order_item_post_save, sender=OrderItem)

        # Perform health checks if not in debug mode
        if not getattr(settings, 'DEBUG', True):
            self._check_service_dependencies()

        logger.info("Order service initialized successfully")

    def _check_service_dependencies(self):
        """
        Check if required services are available.
        This is a lightweight check to ensure the service can start properly.
        """
        product_service_url = getattr(settings, "PRODUCT_SERVICE_URL", None)

        if not product_service_url:
            logger.warning("PRODUCT_SERVICE_URL is not set in settings.")
            return

        try:
            response = requests.get(f"{product_service_url}/health/", timeout=2)
            if response.status_code == 200:
                logger.info(f"Product service is available at {product_service_url}")
            else:
                logger.warning(
                    f"Product service returned status {response.status_code}. "
                    f"Order service will operate in degraded mode."
                )
        except RequestException as e:
            logger.warning(
                f"Could not connect to product service: {str(e)}. "
                f"Order service will operate in degraded mode."
            )
