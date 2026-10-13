from django.contrib import admin
from .models import Wallet, WalletTransaction


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('retailer', 'balance', 'updated_at')
    search_fields = ('retailer__name', 'retailer__phone')
    readonly_fields = ('balance', 'created_at', 'updated_at')


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'wallet', 'type', 'amount', 'balance_after', 'reason')
    list_filter = ('type', 'created_at')
    search_fields = ('wallet__retailer__name', 'reference', 'reason')
    date_hierarchy = 'created_at'
    readonly_fields = ('wallet', 'type', 'amount', 'balance_after', 'reason', 'reference', 'created_by', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
