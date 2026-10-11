from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import timedelta, datetime

from accounts.decorators import role_required
from orders.models import Bakery, Retailer, Product, Order, OrderItem
from .forms import ProductForm, BakerySettingsForm, BakerySetupForm


# ============================================================
# HELPERS
# ============================================================
def get_bakery(user):
    """Return the Bakery for this user, or None."""
    return getattr(user, 'bakery', None)


def tomorrow():
    return timezone.localdate() + timedelta(days=1)


def today():
    return timezone.localdate()


def cutoff_dt_for(bakery, delivery_date):
    """Return the exact datetime when ordering locks for a delivery date."""
    return timezone.make_aware(
        datetime.combine(delivery_date - timedelta(days=1), bakery.cutoff_time)
    )

# ============================================================
# SETUP — create the Bakery business profile (first-time only)
# ============================================================
@role_required('bakery')
def setup(request):
    """
    First-time setup for bakery owners. Collects business details
    and creates the Bakery object. Once created, this page is
    no longer accessible — visitors get redirected to the dashboard.
    """

    # Already set up? Send them away
    if hasattr(request.user, 'bakery'):
        return redirect('bakery:dashboard')

    form = BakerySetupForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        bakery = form.save(commit=False)
        bakery.user = request.user
        bakery.is_active = True
        bakery.save()

        # Assign slug now that the object exists
        if not bakery.slug:
            from orders.models import unique_slug
            bakery.slug = unique_slug(Bakery, bakery.name, max_length=80)
            bakery.save(update_fields=['slug'])

        messages.success(
            request,
            f"{bakery.name} is ready. Retailers can now find you and place orders."
        )
        return redirect('bakery:dashboard')

    return render(request, 'bakery/setup.html', {
        'form': form,
    })

# ============================================================
# DASHBOARD
# ============================================================
@role_required('bakery')
def dashboard(request):
    bakery = get_bakery(request.user)
    if not bakery:
        return render(request, 'bakery:setup')

    delivery_date = tomorrow()
    cutoff_dt = cutoff_dt_for(bakery, delivery_date)

    # Tomorrow's orders
    tomorrow_orders = Order.objects.filter(
        bakery=bakery, delivery_date=delivery_date,
    ).select_related('retailer')

    # Stats
    order_count = tomorrow_orders.count()
    total_loaves = OrderItem.objects.filter(
        order__in=tomorrow_orders
    ).aggregate(total=Sum('quantity'))['total'] or 0
    total_revenue = tomorrow_orders.aggregate(total=Sum('total_amount'))['total'] or 0

    # Pending retailers waiting for approval
    pending_retailers_count = Retailer.objects.filter(
        bakery=bakery, is_active=False
    ).count()

    # Quick product summary (top 3)
    product_summary = (
        OrderItem.objects
        .filter(order__in=tomorrow_orders)
        .values('product__name', 'product__unit')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')[:3]
    )

    return render(request, 'bakery/dashboard.html', {
        'bakery': bakery,
        'delivery_date': delivery_date,
        'cutoff_dt': cutoff_dt,
        'cutoff_passed': timezone.now() >= cutoff_dt,
        'order_count': order_count,
        'total_loaves': total_loaves,
        'total_revenue': total_revenue,
        'pending_retailers_count': pending_retailers_count,
        'product_summary': product_summary,
        'recent_orders': tomorrow_orders.order_by('-placed_at')[:5],
    })

# ============================================================
# ORDERS LIST
# ============================================================
@role_required('bakery')
def orders_list(request):
    bakery = get_bakery(request.user)
    if not bakery:
        return redirect('bakery:setup')

    status = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')

    qs = Order.objects.filter(bakery=bakery).select_related('retailer').prefetch_related('items')

    if status in dict(Order.STATUS_CHOICES):
        qs = qs.filter(status=status)

    if date_filter == 'tomorrow':
        qs = qs.filter(delivery_date=tomorrow())
    elif date_filter == 'today':
        qs = qs.filter(delivery_date=today())
    elif date_filter == 'past':
        qs = qs.filter(delivery_date__lt=today())

    qs = qs.order_by('-delivery_date', '-placed_at')

    return render(request, 'bakery/orders.html', {
        'bakery': bakery,
        'orders': qs,
        'status_filter': status,
        'date_filter': date_filter,
        'status_choices': Order.STATUS_CHOICES,
    })


# ============================================================
# ORDER DETAIL + STATUS UPDATE
# ============================================================
@role_required('bakery')
def order_detail(request, order_id):
    bakery = get_bakery(request.user)
    if not bakery:
        return redirect('bakery:setup')

    order = get_object_or_404(
        Order.objects.select_related('retailer').prefetch_related('items__product'),
        id=order_id,
        bakery=bakery,
    )

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save(update_fields=['status', 'updated_at'])
            messages.success(request, f"Order #{order.id} marked as {order.get_status_display()}.")
        return redirect('bakery:order_detail', order_id=order.id)

    return render(request, 'bakery/order_detail.html', {
        'bakery': bakery,
        'order': order,
        'status_choices': Order.STATUS_CHOICES,
    })


# ============================================================
# PRODUCTION SHEET (THE BAKE LIST)
# ============================================================
@role_required('bakery')
def production(request):
    bakery = get_bakery(request.user)
    if not bakery:
        return redirect('bakery:setup')

    # Allow picking a date; default to tomorrow
    date_str = request.GET.get('date')
    if date_str:
        try:
            delivery_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            delivery_date = tomorrow()
    else:
        delivery_date = tomorrow()

    # Aggregate loaves per product
    production_lines = (
        OrderItem.objects
        .filter(
            order__bakery=bakery,
            order__delivery_date=delivery_date,
        )
        .exclude(order__status='cancelled')
        .values('product__name', 'product__unit')
        .annotate(
            total_qty=Sum('quantity'),
            retailer_count=Count('order__retailer', distinct=True),
        )
        .order_by('-total_qty')
    )

    # Per-retailer breakdown
    retailer_breakdown = (
        Order.objects
        .filter(bakery=bakery, delivery_date=delivery_date)
        .exclude(status='cancelled')
        .select_related('retailer')
        .prefetch_related('items__product')
        .order_by('retailer__name')
    )

    grand_total = sum(line['total_qty'] for line in production_lines)

    return render(request, 'bakery/production.html', {
        'bakery': bakery,
        'delivery_date': delivery_date,
        'production_lines': production_lines,
        'retailer_breakdown': retailer_breakdown,
        'grand_total': grand_total,
    })


# ============================================================
# PRODUCTS
# ============================================================
@role_required('bakery')
def products_list(request):
    bakery = get_bakery(request.user)
    if not bakery:
        return redirect('bakery:setup')

    products = bakery.products.order_by('name')

    return render(request, 'bakery/products.html', {
        'bakery': bakery,
        'products': products,
    })


@role_required('bakery')
def product_new(request):
    bakery = get_bakery(request.user)
    if not bakery:
        return redirect('bakery:setup')

    form = ProductForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        product = form.save(commit=False)
        product.bakery = bakery
        product.save()
        messages.success(request, f"'{product.name}' added to the catalog.")
        return redirect('bakery:products_list')

    return render(request, 'bakery/product_form.html', {
        'bakery': bakery,
        'form': form,
        'is_edit': False,
    })


@role_required('bakery')
def product_edit(request, slug):
    bakery = get_bakery(request.user)
    if not bakery:
        return redirect('bakery:setup')

    product = get_object_or_404(Product, bakery=bakery, slug=slug)

    form = ProductForm(request.POST or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f"'{product.name}' updated.")
        return redirect('bakery:products_list')

    return render(request, 'bakery/product_form.html', {
        'bakery': bakery,
        'form': form,
        'product': product,
        'is_edit': True,
    })


@role_required('bakery')
def product_toggle(request, slug):
    if request.method != 'POST':
        return redirect('bakery:setup')

    bakery = get_bakery(request.user)
    if not bakery:
        return redirect('bakery:dashboard')

    product = get_object_or_404(Product, bakery=bakery, slug=slug)
    product.is_available = not product.is_available
    product.save(update_fields=['is_available'])

    state = 'available' if product.is_available else 'unavailable'
    messages.success(request, f"'{product.name}' is now {state}.")
    return redirect('bakery:products_list')


# ============================================================
# RETAILERS
# ============================================================
@role_required('bakery')
def retailers_list(request):
    bakery = get_bakery(request.user)
    if not bakery:
        return redirect('bakery:setup')

    qs = bakery.retailers.order_by('-is_active', 'name')
    return render(request, 'bakery/retailers.html', {
        'bakery': bakery,
        'retailers': qs,
        'pending_count': qs.filter(is_active=False).count(),
        'active_count': qs.filter(is_active=True).count(),
    })


@role_required('bakery')
def retailer_detail(request, slug):
    bakery = get_bakery(request.user)
    if not bakery:
        return redirect('bakery:dashboard')

    retailer = get_object_or_404(Retailer, bakery=bakery, slug=slug)
    recent_orders = retailer.orders.order_by('-delivery_date')[:10]

    return render(request, 'bakery/retailer_detail.html', {
        'bakery': bakery,
        'retailer': retailer,
        'recent_orders': recent_orders,
    })


@role_required('bakery')
def retailer_toggle(request, slug):
    if request.method != 'POST':
        return redirect('bakery:setup')

    bakery = get_bakery(request.user)
    if not bakery:
        return redirect('bakery:dashboard')

    retailer = get_object_or_404(Retailer, bakery=bakery, slug=slug)
    retailer.is_active = not retailer.is_active
    retailer.save(update_fields=['is_active'])

    # Notify the retailer
    from notifications.services import (
        notify_retailer_approved,
        notify_retailer_suspended,
    )
    if retailer.is_active:
        notify_retailer_approved(retailer)
        state = 'approved'
    else:
        notify_retailer_suspended(retailer)
        state = 'suspended'

    messages.success(request, f"'{retailer.name}' is now {state}.")
    return redirect('bakery:retailers_list')


# ============================================================
# DELIVERIES
# ============================================================
@role_required('bakery')
def deliveries(request):
    bakery = get_bakery(request.user)
    if not bakery:
        return redirect('bakery:setup')

    date_str = request.GET.get('date')
    if date_str:
        try:
            delivery_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            delivery_date = tomorrow()
    else:
        delivery_date = tomorrow()

    orders = (
        Order.objects
        .filter(bakery=bakery, delivery_date=delivery_date)
        .exclude(status='cancelled')
        .select_related('retailer')
        .prefetch_related('items__product')
        .order_by('retailer__name')
    )

    total_stops = orders.count()
    total_loaves = sum(o.total_loaves for o in orders)

    return render(request, 'bakery/deliveries.html', {
        'bakery': bakery,
        'delivery_date': delivery_date,
        'orders': orders,
        'total_stops': total_stops,
        'total_loaves': total_loaves,
    })


# ============================================================
# SETTINGS
# ============================================================
@role_required('bakery')
def settings_view(request):
    bakery = get_bakery(request.user)
    if not bakery:
        return redirect('bakery:setup')

    form = BakerySettingsForm(request.POST or None, instance=bakery)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Settings updated.')
        return redirect('bakery:settings_view')

    return render(request, 'bakery/settings.html', {
        'bakery': bakery,
        'form': form,
    })
