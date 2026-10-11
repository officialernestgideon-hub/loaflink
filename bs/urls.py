"""
URL configuration for bs project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin as django_admin
from django.urls import include, path

django_admin.site.site_header = 'LoafLink Admin'
django_admin.site.site_title = 'LoafLink'
django_admin.site.index_title = 'Bakery & Orders Management'

urlpatterns = [
    path('django-admin/', django_admin.site.urls),
    path('admin/', include("console.urls")),
    path('accounts/', include('accounts.urls')),
    path('shop/', include("shop.urls")),
    path('bakery/', include("bakery.urls")),
    path('', include("breadlink.urls")),
]
