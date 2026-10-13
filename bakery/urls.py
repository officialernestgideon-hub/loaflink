from django.urls import path
from . import views

app_name = 'bakery'

urlpatterns = [
    path('setup/', views.setup, name='setup'),
    path('', views.dashboard, name='dashboard'),
    path('orders/', views.orders_list, name='orders_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('production/', views.production, name='production'),

    path('products/', views.products_list, name='products_list'),
    path('products/new/', views.product_new, name='product_new'),
    path('products/<slug:slug>/edit/', views.product_edit, name='product_edit'),
    path('products/<slug:slug>/toggle/', views.product_toggle, name='product_toggle'),

    path('retailers/', views.retailers_list, name='retailers_list'),
    path('retailers/<slug:slug>/', views.retailer_detail, name='retailer_detail'),
    path('retailers/<slug:slug>/toggle/', views.retailer_toggle, name='retailer_toggle'),
    path('retailers/<slug:slug>/topup/', views.retailer_topup, name='retailer_topup'),

    path('deliveries/', views.deliveries, name='deliveries'),
    path('settings/', views.settings_view, name='settings_view'),
    path('more/', views.more_menu, name='more'),
]