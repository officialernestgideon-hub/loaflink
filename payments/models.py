from django.db import models
from django.db.models import Sum
from decimal import Decimal

from orders.models import Retailer


class Wallet(models.Model):
    """
    One wallet per retailer. Prepaid balance used to pay for orders.
    """

    retailer = models.OneToOneField(
        Retailer,
        on_delete=models.CASCADE,
        related_name='wallet',
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Current wallet balance. Never negative.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Wallet'
        verbose_name_plural = 'Wallets'

    def __str__(self):
        return f'{self.retailer.name} — ₦{self.balance}'

    # ---------- Ledger-driven operations ----------

    def credit(self, amount, reason='Top-up', reference='', created_by=None):
        """Add money to the wallet and log the transaction."""
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError('Credit amount must be positive.')

        self.balance = self.balance + amount
        self.save(update_fields=['balance', 'updated_at'])

        return WalletTransaction.objects.create(
            wallet=self,
            type='credit',
            amount=amount,
            balance_after=self.balance,
            reason=reason,
            reference=reference,
            created_by=created_by,
        )

    def debit(self, amount, reason='Order payment', reference='', created_by=None):
        """Remove money from the wallet. Refuses to go below zero."""
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError('Debit amount must be positive.')

        if self.balance < amount:
            raise ValueError(
                f'Insufficient balance. Wallet has ₦{self.balance}, '
                f'but ₦{amount} is required.'
            )

        self.balance = self.balance - amount
        self.save(update_fields=['balance', 'updated_at'])

        return WalletTransaction.objects.create(
            wallet=self,
            type='debit',
            amount=amount,
            balance_after=self.balance,
            reason=reason,
            reference=reference,
            created_by=created_by,
        )

    def has_enough_for(self, amount):
        return self.balance >= Decimal(str(amount))


class WalletTransaction(models.Model):
    """
    Immutable ledger of every wallet movement.
    """

    TYPE_CHOICES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
        ('refund', 'Refund'),
        ('adjustment', 'Adjustment'),
    ]

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions',
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)

    reason = models.CharField(max_length=200, blank=True)
    reference = models.CharField(
        max_length=100, blank=True,
        help_text='Order ID, top-up ref, etc.',
    )

    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='wallet_actions',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Wallet Transaction'
        verbose_name_plural = 'Wallet Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', '-created_at']),
        ]

    def __str__(self):
        sign = '+' if self.type in ('credit', 'refund') else '−'
        return f'{sign}₦{self.amount} · {self.wallet.retailer.name}'


# ============================================================
# SIGNALS — auto-create a wallet for every new retailer
# ============================================================
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Retailer)
def ensure_wallet_exists(sender, instance, created, **kwargs):
    """Every retailer gets a wallet — created automatically."""
    if created:
        Wallet.objects.get_or_create(retailer=instance)
