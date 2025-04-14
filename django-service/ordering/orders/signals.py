# orders/signals.py

import json
import logging
import requests
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from requests.exceptions import RequestException
from .models import Order, OrderItem  # Ensure you import the actual models

logger = logging.getLogger(__name__)

def publish_event(event_type, event_data):
    """
    Publish an event to other microservices.
    In production, use message brokers like Kafka/RabbitMQ.
    This uses HTTP webhooks for simplicity.
    """
    if not hasattr(settings, 'EVENT_SERVICE_URL'):
        logger.debug(f"Skipping event publishing for {event_type} (no EVENT_SERVICE_URL configured)")
        return

    try:
        payload = {
            'type': event_type,
            'service': getattr(settings, 'SERVICE_NAME', 'orders'),
            'data': event_data
        }

        response = requests.post(
            settings.EVENT_SERVICE_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=1
        )

        if response.status_code != 200:
            logger.warning(f"Failed to publish {event_type} event: {response.status_code}")
    except RequestException as e:
        logger.warning(f"Error publishing {event_type} event: {str(e)}")

@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    """
    Handle order creation and updates.
    """
    event_data = {
        'order_id': str(instance.id),
        'status': instance.status,
        'total_price': float(instance.total_price) if instance.total_price else 0,
        'user_id': instance.user.id if instance.user else None,
        'created_at': instance.created_at.isoformat() if instance.created_at else None,
        'updated_at': instance.updated_at.isoformat() if instance.updated_at else None,
    }

    if created:
        publish_event('order.created', event_data)
        logger.info(f"Order created: {instance.id}")
    else:
        publish_event('order.updated', event_data)
        logger.info(f"Order updated: {instance.id} (status: {instance.status})")

@receiver(post_delete, sender=Order)
def order_post_delete(sender, instance, **kwargs):
    """
    Handle order deletion.
    """
    event_data = {
        'order_id': str(instance.id),
        'user_id': instance.user.id if instance.user else None,
    }

    publish_event('order.deleted', event_data)
    logger.info(f"Order deleted: {instance.id}")

@receiver(post_save, sender=OrderItem)
def order_item_post_save(sender, instance, created, **kwargs):
    """
    Handle order item creation and updates.
    """
    order = instance.order
    if hasattr(order, 'recalculate_total'):
        order.recalculate_total()

    if created:
        event_data = {
            'order_id': str(order.id),
            'item_id': str(instance.id),
            'product_id': instance.product.id if instance.product else None,
            'quantity': instance.quantity,
        }

        publish_event('order_item.created', event_data)
        logger.debug(f"Order item created: {instance.id} for order {order.id}")
