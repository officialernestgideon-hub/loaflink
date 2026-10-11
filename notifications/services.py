"""
Notification services.

Central place for sending SMS/WhatsApp. Swap the backend by changing
SMS_PROVIDER in settings. Currently supports:

- 'console'      → prints to terminal (dev)
- 'termii'       → Termii API (add your key in settings)

To add Twilio/Africa's Talking later, just add a new elif branch.
"""

from django.conf import settings
from .models import NotificationLog


# ============================================================
# LOW-LEVEL: send one SMS
# ============================================================
def send_sms(phone, message, related_user=None, channel='sms'):
    """
    Send an SMS via the configured provider.
    Returns True on success, False on failure.
    Always logs to NotificationLog.
    """
    provider = getattr(settings, 'SMS_PROVIDER', 'console')

    try:
        if provider == 'console':
            _send_console(phone, message)
            success = True
            error = ''

        elif provider == 'termii':
            success, error = _send_termii(phone, message)

        else:
            success = False
            error = f'Unknown provider: {provider}'

    except Exception as e:
        success = False
        error = str(e)

    NotificationLog.objects.create(
        channel=channel,
        recipient=phone,
        message=message,
        status='sent' if success else 'failed',
        error_message=error,
        related_user=related_user,
    )

    return success


# ============================================================
# PROVIDERS
# ============================================================
def _send_console(phone, message):
    """Dev provider — prints the message to the Django terminal."""
    border = '─' * 60
    print(f'\n{border}')
    print(f'  📱  SMS → {phone}')
    print(f'{border}')
    for line in message.split('\n'):
        print(f'  {line}')
    print(f'{border}\n')


def _send_termii(phone, message):
    """
    Termii SMS provider (Nigeria, Ghana, Kenya).
    Docs: https://developers.termii.com/
    """
    import requests

    api_key = getattr(settings, 'TERMII_API_KEY', '')
    sender_id = getattr(settings, 'TERMII_SENDER_ID', 'LoafLink')

    if not api_key:
        return False, 'TERMII_API_KEY not set in settings'

    # Termii expects phone without leading +
    clean_phone = phone.lstrip('+')

    payload = {
        'to': clean_phone,
        'from': sender_id,
        'sms': message,
        'type': 'plain',
        'channel': 'generic',
        'api_key': api_key,
    }

    try:
        r = requests.post(
            'https://api.ng.termii.com/api/sms/send',
            json=payload,
            timeout=10,
        )
        data = r.json()
        if r.status_code == 200 and data.get('code') == 'ok':
            return True, ''
        return False, data.get('message', 'Termii error')
    except Exception as e:
        return False, f'Termii request failed: {e}'


# ============================================================
# HIGH-LEVEL: notification helpers
# ============================================================
def notify_new_order(order):
    """Send the bakery a WhatsApp-style notification about a new order."""
    bakery_user = order.bakery.user
    phone = bakery_user.phone

    lines = [
        f'🥖 New order for {order.delivery_date.strftime("%a, %d %b")}',
        f'',
        f'From: {order.retailer.name}',
        f'Items:',
    ]
    for item in order.items.all():
        lines.append(f'  • {item.quantity} × {item.product.name}')

    lines += [
        '',
        f'Total: ₦{order.total_amount}',
        f'',
        f'View in dashboard → loaflink.app/bakery/orders/{order.id}/',
    ]

    message = '\n'.join(lines)
    return send_sms(phone, message, related_user=bakery_user, channel='whatsapp')


def notify_status_change(order, old_status):
    """Notify the retailer when their order status changes."""
    retailer_user = order.retailer.user
    phone = retailer_user.phone

    status_labels = {
        'locked': 'locked',
        'baking': 'being baked',
        'out_for_delivery': 'out for delivery',
        'delivered': 'delivered',
        'cancelled': 'cancelled',
    }

    label = status_labels.get(order.status, order.get_status_display().lower())

    message = (
        f'Hi {order.retailer.name},\n\n'
        f'Your order #{order.id} for {order.delivery_date.strftime("%a, %d %b")} '
        f'is now {label}.\n\n'
        f'LoafLink'
    )

    return send_sms(phone, message, related_user=retailer_user, channel='sms')


def notify_retailer_approved(retailer):
    """Tell a retailer they've been approved."""
    user = retailer.user
    message = (
        f'🎉 You\'ve been approved!\n\n'
        f'{retailer.bakery.name} has approved your shop on LoafLink.\n\n'
        f'Log in to start ordering bread:\n'
        f'loaflink.app/accounts/login/\n\n'
        f'LoafLink'
    )
    return send_sms(user.phone, message, related_user=user, channel='sms')


def notify_retailer_suspended(retailer):
    """Tell a retailer their account has been suspended."""
    user = retailer.user
    message = (
        f'Your LoafLink account has been paused.\n\n'
        f'{retailer.bakery.name} has temporarily suspended your ordering access.\n\n'
        f'Contact them directly if you have questions.\n\n'
        f'LoafLink'
    )
    return send_sms(user.phone, message, related_user=user, channel='sms')


def notify_cutoff_reminder(retailer, cutoff_time):
    """Remind a retailer who hasn't ordered yet."""
    user = retailer.user
    tomorrow_str = (retailer.bakery and '') or ''
    message = (
        f'⏰ Order cutoff at {cutoff_time.strftime("%I:%M %p")}\n\n'
        f'Hi {retailer.name}, you haven\'t placed your order for '
        f'tomorrow yet.\n\n'
        f'Order now: loaflink.app/shop/catalog/\n\n'
        f'LoafLink'
    )
    return send_sms(user.phone, message, related_user=user, channel='whatsapp')


def notify_cutoff_passed(bakery, delivery_date, total_loaves, order_count):
    """Alert the bakery that the order window has closed."""
    user = bakery.user
    message = (
        f'🔔 Order window closed\n\n'
        f'{order_count} orders received for {delivery_date.strftime("%a, %d %b")}\n'
        f'Total loaves to bake: {total_loaves}\n\n'
        f'View bake list → loaflink.app/bakery/production/\n\n'
        f'LoafLink'
    )
    return send_sms(user.phone, message, related_user=user, channel='whatsapp')