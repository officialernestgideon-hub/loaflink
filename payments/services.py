from decimal import Decimal
from .models import Wallet


def get_wallet(retailer):
    """Return the retailer's wallet, creating it if it doesn't exist."""
    wallet, _ = Wallet.objects.get_or_create(retailer=retailer)
    return wallet


def credit_wallet(retailer, amount, reason='Top-up', reference='', created_by=None):
    """Top up a retailer's wallet."""
    wallet = get_wallet(retailer)
    return wallet.credit(amount, reason=reason, reference=reference, created_by=created_by)


def debit_wallet(retailer, amount, reason='Order payment', reference='', created_by=None):
    """Debit a retailer's wallet — raises ValueError if insufficient."""
    wallet = get_wallet(retailer)
    return wallet.debit(amount, reason=reason, reference=reference, created_by=created_by)


def refund_wallet(retailer, amount, reason='Order cancelled', reference='', created_by=None):
    """Refund a debit. Uses credit() under the hood but tags type as refund."""
    from .models import WalletTransaction

    wallet = get_wallet(retailer)
    amount = Decimal(str(amount))

    wallet.balance = wallet.balance + amount
    wallet.save(update_fields=['balance', 'updated_at'])

    return WalletTransaction.objects.create(
        wallet=wallet,
        type='refund',
        amount=amount,
        balance_after=wallet.balance,
        reason=reason,
        reference=reference,
        created_by=created_by,
    )


def can_afford(retailer, amount):
    """True if the retailer's wallet can cover the given amount."""
    wallet = get_wallet(retailer)
    return wallet.has_enough_for(amount)