from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from datetime import timedelta

from accounts.decorators import role_required
from orders.models import Product, Retailer, Order, OrderItem, Bakery
from .cart import Cart
from .forms import BakerySelectForm



# ============================================================
# HELPERS
# ============================================================
def get_retailer_or_none(user):
    """Return the Retailer profile for this user, or None if missing."""
    return getattr(user, 'retailer', None)


def get_cutoff_datetime(retailer, delivery_date):
    """Return the datetime when orders lock for the given delivery date."""
    cutoff = retailer.bakery.cutoff_time
    return timezone.make_aware(
        timezone.datetime.combine(delivery_date - timedelta(days=1), cutoff)
    )


def next_delivery_date():
    """Tomorrow — the earliest possible delivery date for a fresh order."""
    return timezone.localdate() + timedelta(days=1)


def can_order_now(retailer):
    """True if the bakery cutoff has not yet passed for tomorrow's delivery."""
    cutoff_dt = get_cutoff_datetime(retailer, next_delivery_date())
    return timezone.now() < cutoff_dt


# ============================================================
# HOME
# ============================================================
@role_required('retailer')
def home(request):
    retailer = get_retailer_or_none(request.user)
    if not retailer:
        return render(request, 'shop/no_profile.html')
    
    if not retailer:
        redirect('shop:setup')

    if not retailer.is_active:
        return render(request, 'shop/pending_approval.html', {'retailer': retailer})

    delivery_date = next_delivery_date()
    today_order = Order.objects.filter(
        retailer=retailer, delivery_date=delivery_date
    ).first()

    recent_orders = retailer.orders.exclude(
        delivery_date=delivery_date
    )[:5]

    cart = Cart(request)

    return render(request, 'shop/home.html', {
        'retailer': retailer,
        'bakery': retailer.bakery,
        'delivery_date': delivery_date,
        'cutoff_dt': get_cutoff_datetime(retailer, delivery_date),
        'today_order': today_order,
        'recent_orders': recent_orders,
        'cart_count': len(cart),
        'can_order': can_order_now(retailer),
    })
    
# ============================================================
# SETUP — link retailer to a bakery
# ============================================================
@role_required('retailer')
def setup(request):
    """
    First-time setup for retailers who don't have a Retailer profile yet.
    They pick a bakery + enter their delivery address. The profile is
    created with is_active=False so the bakery can approve it.
    """

    # If they already have a profile, send them back to home
    if get_retailer_or_none(request.user):
        return redirect('shop:home')

    # If no bakeries exist at all, show an informative page
    if not Bakery.objects.filter(is_active=True).exists():
        return render(request, 'shop/setup.html', {
            'no_bakeries': True,
        })

    form = BakerySelectForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        bakery = form.cleaned_data['bakery']
        address = form.cleaned_data['address'].strip()

        Retailer.objects.create(
            user=request.user,
            bakery=bakery,
            name=request.user.full_name or f'Shop {request.user.phone[-4:]}',
            phone=request.user.phone,
            state=form.cleaned_data['state'],
            address=address,
            is_active=False,   # Bakery must approve
        )

        messages.success(
            request,
            f"You're linked to {bakery.name}. "
            "The bakery will review your account shortly."
        )
        return redirect('shop:home')

    return render(request, 'shop/setup.html', {
        'form': form,
        'no_bakeries': False,
    })

# ============================================================
# CATALOG
# ============================================================
@role_required('retailer')
def catalog(request):
    retailer = get_retailer_or_none(request.user)
    if not retailer or not retailer.is_active:
        return redirect('shop:home')

    products = Product.objects.filter(
        bakery=retailer.bakery,
        is_available=True,
    ).order_by('name')

    cart = Cart(request)
    cart_quantities = {pid: qty for pid, qty in cart.cart.items()}

    return render(request, 'shop/catalog.html', {
        'retailer': retailer,
        'bakery': retailer.bakery,
        'products': products,
        'cart_quantities': cart_quantities,
        'cart_count': len(cart),
        'cart_total': cart.total(),
        'can_order': can_order_now(retailer),
        'delivery_date': next_delivery_date(),
    })


# ============================================================
# CART ACTIONS
# ============================================================
@role_required('retailer')
def cart_add(request, product_id):
    if request.method != 'POST':
        return redirect('shop:catalog')

    retailer = get_retailer_or_none(request.user)
    if not retailer or not retailer.is_active:
        return redirect('shop:home')

    product = get_object_or_404(Product, id=product_id, bakery=retailer.bakery)
    qty = int(request.POST.get('quantity', 1) or 1)

    if not can_order_now(retailer):
        messages.error(request, "Order cutoff has passed for tomorrow. Try again tomorrow morning.")
        return redirect('shop:catalog')

    cart = Cart(request)
    cart.add(product, qty)
    messages.success(request, f"Added {qty} × {product.name} to your order.")
    return redirect(request.POST.get('next') or 'shop:catalog')


@role_required('retailer')
def cart_remove(request, product_id):
    if request.method != 'POST':
        return redirect('shop:cart')

    product = get_object_or_404(Product, id=product_id)
    Cart(request).remove(product)
    messages.success(request, f"Removed {product.name}.")
    return redirect('shop:cart')


@role_required('retailer')
def cart_view(request):
    retailer = get_retailer_or_none(request.user)
    if not retailer or not retailer.is_active:
        return redirect('shop:home')

    cart = Cart(request)
    return render(request, 'shop/cart.html', {
        'retailer': retailer,
        'cart_lines': list(cart),
        'cart_total': cart.total(),
        'cart_count': len(cart),
        'can_order': can_order_now(retailer),
        'delivery_date': next_delivery_date(),
    })


@role_required('retailer')
def cart_clear(request):
    if request.method == 'POST':
        Cart(request).clear()
        messages.success(request, "Cart cleared.")
    return redirect('shop:cart')


# ============================================================
# CHECKOUT
# ============================================================
@role_required('retailer')
def checkout(request):
    retailer = get_retailer_or_none(request.user)
    if not retailer or not retailer.is_active:
        return redirect('shop:home')

    cart = Cart(request)
    if cart.is_empty():
        messages.error(request, "Your cart is empty.")
        return redirect('shop:catalog')

    delivery_date = next_delivery_date()
    cutoff_dt = get_cutoff_datetime(retailer, delivery_date)

    if timezone.now() >= cutoff_dt:
        messages.error(
            request,
            "The cutoff for tomorrow's delivery has passed. "
            "Please try again before 8:00 PM today."
        )
        return redirect('shop:cart')

    # Prevent duplicate order for the same delivery date
    if Order.objects.filter(retailer=retailer, delivery_date=delivery_date).exists():
        messages.error(request, "You already placed an order for tomorrow.")
        return redirect('shop:orders')

    if request.method == 'POST':
        notes = request.POST.get('notes', '').strip()[:300]

        with transaction.atomic():
            order = Order.objects.create(
                retailer=retailer,
                bakery=retailer.bakery,
                delivery_date=delivery_date,
                status='pending',
                notes=notes,
            )

            for line in cart:
                OrderItem.objects.create(
                    order=order,
                    product=line['product'],
                    quantity=line['quantity'],
                    unit_price=line['unit_price'],
                )

            order.recalculate_total()

        cart.clear()
        
        # Notify the bakery of the new order
        from notifications.services import notify_new_order
        notify_new_order(order)
        
        messages.success(request, f"Order #{order.id} placed for {delivery_date.strftime('%a, %d %b')}.")
        return redirect('shop:order_detail', order_id=order.id)

    return render(request, 'shop/checkout.html', {
        'retailer': retailer,
        'cart_lines': list(cart),
        'cart_total': cart.total(),
        'cart_count': len(cart),
        'delivery_date': delivery_date,
        'cutoff_dt': cutoff_dt,
    })


# ============================================================
# ORDERS
# ============================================================
@role_required('retailer')
def orders(request):
    retailer = get_retailer_or_none(request.user)
    if not retailer or not retailer.is_active:
        return redirect('shop:home')

    qs = retailer.orders.select_related('bakery').prefetch_related('items__product')
    return render(request, 'shop/orders.html', {
        'retailer': retailer,
        'orders': qs,
        'cart_count': len(Cart(request)),
    })


@role_required('retailer')
def order_detail(request, order_id):
    retailer = get_retailer_or_none(request.user)
    if not retailer or not retailer.is_active:
        return redirect('shop:home')

    order = get_object_or_404(
        Order.objects.select_related('bakery').prefetch_related('items__product'),
        id=order_id,
        retailer=retailer,
    )

    return render(request, 'shop/order_detail.html', {
        'retailer': retailer,
        'order': order,
        'cart_count': len(Cart(request)),
        'can_reorder': can_order_now(retailer) and order.delivery_date < next_delivery_date(),
    })


@role_required('retailer')
def reorder(request, order_id):
    """Load a past order's items into the cart."""
    if request.method != 'POST':
        return redirect('shop:orders')

    retailer = get_retailer_or_none(request.user)
    if not retailer or not retailer.is_active:
        return redirect('shop:home')

    if not can_order_now(retailer):
        messages.error(request, "Cutoff has passed. Try again before 8:00 PM tomorrow.")
        return redirect('shop:orders')

    past_order = get_object_or_404(Order, id=order_id, retailer=retailer)

    cart = Cart(request)
    cart.clear()
    for item in past_order.items.all():
        # Only re-add if product is still available
        if item.product.is_available and item.product.bakery_id == retailer.bakery_id:
            cart.add(item.product, item.quantity)

    messages.success(request, f"Loaded {len(cart)} items from order #{past_order.id} into your cart.")
    return redirect('shop:cart')
