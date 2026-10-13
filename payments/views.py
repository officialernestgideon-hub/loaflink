from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from accounts.decorators import role_required
from .models import Wallet, WalletTransaction
from .services import get_wallet


@role_required('retailer')
def wallet_view(request):
    retailer = getattr(request.user, 'retailer', None)
    if not retailer:
        return redirect('shop:setup')

    wallet = get_wallet(retailer)
    transactions = wallet.transactions.select_related('created_by')[:50]

    return render(request, 'payments/wallet.html', {
        'retailer': retailer,
        'wallet': wallet,
        'transactions': transactions,
    })
