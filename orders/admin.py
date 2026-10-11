from django.contrib import admin
from .models import Bakery, Retailer, Product, Order, OrderItem


@admin.register(Bakery)
class BakeryAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'cutoff_time', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'phone')
    readonly_fields = ('slug',)


@admin.register(Retailer)
class RetailerAdmin(admin.ModelAdmin):
    list_display = ('name', 'bakery', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active', 'bakery')
    search_fields = ('name', 'phone')
    list_editable = ('is_active',)
    autocomplete_fields = ('bakery',)
    readonly_fields = ('slug',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'bakery', 'price', 'unit', 'is_available')
    list_filter = ('bakery', 'is_available', 'unit')
    search_fields = ('name',)
    list_editable = ('price', 'is_available')
    readonly_fields = ('slug',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    autocomplete_fields = ('product',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'retailer', 'bakery', 'delivery_date',
        'status', 'total_amount', 'placed_at'
    )
    list_filter = ('status', 'bakery', 'delivery_date')
    search_fields = ('retailer__name', 'retailer__phone')
    date_hierarchy = 'delivery_date'
    inlines = [OrderItemInline]
    readonly_fields = ('placed_at', 'updated_at')

    fieldsets = (
        ('Parties', {'fields': ('bakery', 'retailer')}),
        ('Delivery', {'fields': ('delivery_date', 'status', 'notes')}),
        ('Financials', {'fields': ('total_amount',)}),
        ('Timestamps', {'fields': ('placed_at', 'updated_at')}),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'unit_price', 'subtotal')
    list_filter = ('product',)
    search_fields = ('order__retailer__name', 'product__name')

