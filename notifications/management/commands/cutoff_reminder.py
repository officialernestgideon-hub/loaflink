from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from orders.models import Bakery, Retailer, Order
from notifications.services import notify_cutoff_reminder


class Command(BaseCommand):
    help = 'Send cutoff reminders to retailers who have not ordered for tomorrow.'

    def handle(self, *args, **options):
        tomorrow = timezone.localdate() + timedelta(days=1)
        sent_count = 0

        # For each active bakery
        for bakery in Bakery.objects.filter(is_active=True):
            # Find active retailers who have NOT placed an order for tomorrow
            ordered_retailer_ids = Order.objects.filter(
                bakery=bakery,
                delivery_date=tomorrow,
            ).exclude(status='cancelled').values_list('retailer_id', flat=True)

            pending_retailers = Retailer.objects.filter(
                bakery=bakery,
                is_active=True,
            ).exclude(id__in=ordered_retailer_ids)

            for retailer in pending_retailers:
                notify_cutoff_reminder(retailer, bakery.cutoff_time)
                sent_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Sent {sent_count} cutoff reminder(s) for {tomorrow}.'
        ))