from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta

from orders.models import Bakery, Order, OrderItem
from notifications.services import notify_cutoff_passed


class Command(BaseCommand):
    help = 'Notify bakeries that the cutoff passed, with their bake summary.'

    def handle(self, *args, **options):
        tomorrow = timezone.localdate() + timedelta(days=1)
        sent_count = 0

        for bakery in Bakery.objects.filter(is_active=True):
            orders = Order.objects.filter(
                bakery=bakery,
                delivery_date=tomorrow,
            ).exclude(status='cancelled')

            order_count = orders.count()
            if order_count == 0:
                continue   # nothing to report

            total_loaves = OrderItem.objects.filter(
                order__in=orders
            ).aggregate(total=Sum('quantity'))['total'] or 0

            notify_cutoff_passed(bakery, tomorrow, total_loaves, order_count)
            sent_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Sent {sent_count} cutoff-passed notification(s).'
        ))