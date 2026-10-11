from django.shortcuts import render

# Create your views here.

def home(request):
    context = {
        'brand': 'LoafLink',
        'tagline': 'Bake exactly what sells.',

        'features': [
            {
                'icon': 'fa-solid fa-mobile-screen-button',
                'color': 'purple',
                'title': 'Simple Retailer App',
                'desc': 'Retailers log in with a phone number, browse bread types, and place bulk orders in under 60 seconds.',
            },
            {
                'icon': 'fa-solid fa-clock',
                'color': 'amber',
                'title': '8:00 PM Order Lock',
                'desc': 'Orders close automatically at 8:00 PM sharp. The bakery knows exactly what to bake overnight.',
            },
            {
                'icon': 'fa-solid fa-clipboard-list',
                'color': 'cyan',
                'title': 'Auto Bake List',
                'desc': 'At 8:05 PM, the system generates a precise production sheet for the bakers. Zero math, zero errors.',
            },
            {
                'icon': 'fa-brands fa-whatsapp',
                'color': 'green',
                'title': 'WhatsApp / SMS Alerts',
                'desc': 'Instant order confirmations, cutoff reminders, and delivery updates sent where retailers actually read.',
            },
            {
                'icon': 'fa-solid fa-truck-fast',
                'color': 'pink',
                'title': 'Smart Delivery Manifest',
                'desc': 'Drivers get a printable route sheet grouped by area, with quantities per shop. No more guesswork.',
            },
            {
                'icon': 'fa-solid fa-chart-line',
                'color': 'indigo',
                'title': 'Live Order Dashboard',
                'desc': 'The bakery sees orders come in real time. Track totals, revenue, and loaves per bread type at a glance.',
            },
        ],

        'steps': [
            {'num': '01', 'title': 'Retailer Logs In', 'desc': 'Phone number login. No passwords, no friction.'},
            {'num': '02', 'title': 'Places Bulk Order', 'desc': 'Selects bread types and quantities before 8:00 PM.'},
            {'num': '03', 'title': 'Order Locks', 'desc': 'At 8:00 PM the system locks orders and alerts the bakery.'},
            {'num': '04', 'title': 'Bakery Bakes Exactly', 'desc': 'The Auto Bake List tells bakers precisely what to produce.'},
        ],

        'bakery_points': [
            'Eliminate unsold bread and waste',
            'Get an exact Bake List every night at 8:05 PM',
            'See all orders in real time on one dashboard',
            'Digital ledger — no more paper notebooks',
            'Delivery manifest sorted by route',
        ],

        'retailer_points': [
            'Order in under 60 seconds from your phone',
            'Get instant WhatsApp / SMS confirmations',
            'Never miss the 8:00 PM reminder again',
            'One-tap reorder from your history',
            'Full visibility of pricing and past orders',
        ],
    }
    return render(request, 'breadlink/home.html', context)