from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from orders.models import Order
from notifications.services import notify_status_change


@receiver(pre_save, sender=Order)
def cache_old_status(sender, instance, **kwargs):
    """Store the old status before saving, so post_save can compare."""
    if instance.pk:
        try:
            old = Order.objects.get(pk=instance.pk)
            instance._old_status = old.status
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Order)
def send_status_change_notification(sender, instance, created, **kwargs):
    """Notify the retailer whenever the order status changes."""
    if created:
        return

    old = getattr(instance, '_old_status', None)
    if old and old != instance.status:
        notify_status_change(instance, old)