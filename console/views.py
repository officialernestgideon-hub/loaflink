from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import timedelta

from orders.models import Bakery, Retailer, Product, Order, OrderItem
from notifications.models import NotificationLog
# from payments.models import Wallet
from .decorators import admin_required


def _stats():
    """Compute every metric the dashboard needs. Called once per request."""
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    week_start = today_start - timedelta(days=7)
    month_start = today_start.replace(day=1)

    # Core counts
    active_bakeries = Bakery.objects.filter(is_active=True).count()
    active_retailers = Retailer.objects.filter(is_active=True).count()
    pending_retailers = Retailer.objects.filter(is_active=False).count()

    # Orders today
    orders_today = Order.objects.filter(placed_at__gte=today_start).exclude(status='cancelled')
    orders_today_count = orders_today.count()
    loaves_today = OrderItem.objects.filter(order__in=orders_today).aggregate(t=Sum('quantity'))['t'] or 0

    # Orders yesterday (for comparison)
    orders_yesterday_count = Order.objects.filter(
        placed_at__gte=yesterday_start, placed_at__lt=today_start
    ).exclude(status='cancelled').count()

    # GMV this month
    gmv_month = Order.objects.filter(
        placed_at__gte=month_start
    ).exclude(status='cancelled').aggregate(t=Sum('total_amount'))['t'] or 0

    # Notifications last 24h
    notifs_24h = NotificationLog.objects.filter(
        created_at__gte=now - timedelta(hours=24)
    ).count()

    # ---- CHART 1: Orders per day, last 14 days ----
    orders_chart = []
    for i in range(13, -1, -1):
        day = today_start - timedelta(days=i)
        next_day = day + timedelta(days=1)
        count = Order.objects.filter(
            placed_at__gte=day, placed_at__lt=next_day
        ).exclude(status='cancelled').count()
        orders_chart.append({
            'label': day.strftime('%d %b'),
            'value': count,
        })

    # ---- CHART 2: Loaves per day, last 14 days ----
    loaves_chart = []
    for i in range(13, -1, -1):
        day = today_start - timedelta(days=i)
        next_day = day + timedelta(days=1)
        qty = OrderItem.objects.filter(
            order__placed_at__gte=day,
            order__placed_at__lt=next_day,
        ).exclude(order__status='cancelled').aggregate(t=Sum('quantity'))['t'] or 0
        loaves_chart.append({
            'label': day.strftime('%d %b'),
            'value': qty,
        })

    # ---- CHART 3: Signups per day (bakeries + retailers), last 14 days ----
    signups_chart = []
    for i in range(13, -1, -1):
        day = today_start - timedelta(days=i)
        next_day = day + timedelta(days=1)
        b = Bakery.objects.filter(created_at__gte=day, created_at__lt=next_day).count()
        r = Retailer.objects.filter(created_at__gte=day, created_at__lt=next_day).count()
        signups_chart.append({
            'label': day.strftime('%d %b'),
            'bakeries': b,
            'retailers': r,
        })

    # ---- CHART 4: GMV per day, last 14 days ----
    gmv_chart = []
    for i in range(13, -1, -1):
        day = today_start - timedelta(days=i)
        next_day = day + timedelta(days=1)
        amt = Order.objects.filter(
            placed_at__gte=day, placed_at__lt=next_day
        ).exclude(status='cancelled').aggregate(t=Sum('total_amount'))['t'] or 0
        gmv_chart.append({
            'label': day.strftime('%d %b'),
            'value': float(amt),
        })

    return {
        'active_bakeries': active_bakeries,
        'active_retailers': active_retailers,
        'pending_retailers': pending_retailers,
        'orders_today': orders_today_count,
        'orders_yesterday': orders_yesterday_count,
        'loaves_today': loaves_today,
        'gmv_month': gmv_month,
        'notifs_24h': notifs_24h,

        'orders_chart': orders_chart,
        'loaves_chart': loaves_chart,
        'signups_chart': signups_chart,
        'gmv_chart': gmv_chart,
    }


@admin_required
def dashboard(request):
    context = _stats()

    # Recent activity
    context['recent_orders'] = (
        Order.objects.select_related('retailer', 'bakery')
        .order_by('-placed_at')[:8]
    )
    context['recent_retailers'] = (
        Retailer.objects.select_related('bakery', 'user')
        .order_by('-created_at')[:5]
    )
    context['recent_notifications'] = (
        NotificationLog.objects.order_by('-created_at')[:6]
    )

    return render(request, 'console/dashboard.html', context)


@admin_required
def bakeries(request):
    qs = (
        Bakery.objects.select_related('user')
        .annotate(
            retailer_count=Count('retailers', distinct=True),
            order_count=Count('orders', distinct=True),
        )
        .order_by('-created_at')
    )

    return render(request, 'console/bakeries.html', {
        'bakeries': qs,
    })


@admin_required
def retailers(request):
    qs = (
        Retailer.objects.select_related('bakery', 'user')
        .order_by('-created_at')
    )

    return render(request, 'console/retailers.html', {
        'retailers': qs,
    })


@admin_required
def notifications_view(request):
    logs = NotificationLog.objects.order_by('-created_at')[:200]

    return render(request, 'console/notifications.html', {
        'logs': logs,
    })
