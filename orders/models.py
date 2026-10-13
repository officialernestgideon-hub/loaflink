from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import RegexValidator
from datetime import time
from django.utils.text import slugify


phone_validator = RegexValidator(
    regex=r'^\+?[0-9]{7,15}$',
    message='Enter a valid phone number (7–15 digits, optional + prefix).'
)

def unique_slug(model_class, value, slug_field='slug', scope=None, max_length=80):
    """
    Generate a URL-safe slug from `value`.

    - `scope` is an optional dict of filters to restrict uniqueness
      (e.g. {'bakery': self.bakery} for a Product).
    - If the slug already exists, appends -2, -3, ... until unique.
    """
    base = slugify(value)[:max_length] or 'item'
    slug = base
    counter = 2

    qs = model_class.objects.all()
    if scope:
        qs = qs.filter(**scope)

    while qs.filter(**{slug_field: slug}).exists():
        suffix = f'-{counter}'
        slug = f'{base[:max_length - len(suffix)]}{suffix}'
        counter += 1

    return slug

NIGERIAN_STATES = [
    ('abia', 'Abia'),
    ('adamawa', 'Adamawa'),
    ('akwa_ibom', 'Akwa Ibom'),
    ('anambra', 'Anambra'),
    ('bauchi', 'Bauchi'),
    ('bayelsa', 'Bayelsa'),
    ('benue', 'Benue'),
    ('borno', 'Borno'),
    ('cross_river', 'Cross River'),
    ('delta', 'Delta'),
    ('ebonyi', 'Ebonyi'),
    ('edo', 'Edo'),
    ('ekiti', 'Ekiti'),
    ('enugu', 'Enugu'),
    ('fct', 'FCT — Abuja'),
    ('gombe', 'Gombe'),
    ('imo', 'Imo'),
    ('jigawa', 'Jigawa'),
    ('kaduna', 'Kaduna'),
    ('kano', 'Kano'),
    ('katsina', 'Katsina'),
    ('kebbi', 'Kebbi'),
    ('kogi', 'Kogi'),
    ('kwara', 'Kwara'),
    ('lagos', 'Lagos'),
    ('nasarawa', 'Nasarawa'),
    ('niger', 'Niger'),
    ('ogun', 'Ogun'),
    ('ondo', 'Ondo'),
    ('osun', 'Osun'),
    ('oyo', 'Oyo'),
    ('plateau', 'Plateau'),
    ('rivers', 'Rivers'),
    ('sokoto', 'Sokoto'),
    ('taraba', 'Taraba'),
    ('yobe', 'Yobe'),
    ('zamfara', 'Zamfara'),
]

# ============================================================
# BAKERY
# ============================================================
class Bakery(models.Model):
    """
    A bread producer. Supports multi-bakery from day one.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bakery',
        help_text='The login account for this bakery.'
    )
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=80, unique=True, blank=True) 
    phone = models.CharField(max_length=20, validators=[phone_validator])
    address = models.TextField()
    state = models.CharField( 
        max_length=30,
        choices=NIGERIAN_STATES,
        blank=True,
    )

    cutoff_time = models.TimeField(
        default=time(20, 0),
        help_text='Orders must be placed before this time (default 8:00 PM).'
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Bakery'
        verbose_name_plural = 'Bakeries'
        ordering = ['name']

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Bakery, self.name, max_length=80)
        super().save(*args, **kwargs)

    # def get_absolute_url(self):
    #     from django.urls import reverse
    #     return reverse('orders:bakery_detail', kwargs={'slug': self.slug})


# ============================================================
# RETAILER
# ============================================================
class Retailer(models.Model):
    """
    A shop that buys bread from a specific bakery.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='retailer',
        help_text='The login account for this retailer.'
    )
    bakery = models.ForeignKey(
        Bakery,
        on_delete=models.CASCADE,
        related_name='retailers'
    )
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=80, blank=True)
    phone = models.CharField(max_length=20, validators=[phone_validator])
    address = models.TextField()
    state = models.CharField(
        max_length=30,
        choices=NIGERIAN_STATES,
        blank=True,
    )

    is_active = models.BooleanField(
        default=False,
        help_text='Bakery must approve this retailer before they can place orders.'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Retailer'
        verbose_name_plural = 'Retailers'
        ordering = ['name']
        unique_together = ('bakery', 'phone')

    def __str__(self):
        return f'{self.name} → {self.bakery.name}'
    
    def save(self, *args, **kwargs):
        if not self.slug and self.bakery_id:
            self.slug = unique_slug(
                Retailer,
                self.name,
                scope={'bakery': self.bakery},
                max_length=80,
            )
        super().save(*args, **kwargs)


# ============================================================
# PRODUCT
# ============================================================
class Product(models.Model):
    """
    A bread type sold by a bakery.
    """

    UNIT_CHOICES = [
        ('loaf', 'Loaf'),
        ('pack', 'Pack'),
        ('bag', 'Bag'),
    ]

    bakery = models.ForeignKey(
        Bakery,
        on_delete=models.CASCADE,
        related_name='products'
    )
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=80, blank=True)
    description = models.CharField(max_length=200, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='loaf')
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        help_text='Optional. Shown to retailers when ordering.'
    )

    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['name']
        unique_together = ('bakery', 'name')

    def __str__(self):
        return f'{self.name} ({self.bakery.name})'
    
    def save(self, *args, **kwargs):
        if not self.slug and self.bakery_id:
            self.slug = unique_slug(
                Product,
                self.name,
                scope={'bakery': self.bakery},
                max_length=80,
            )
        super().save(*args, **kwargs)


# ============================================================
# ORDER
# ============================================================
class Order(models.Model):
    """
    A retailer's daily order from a specific bakery.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('locked', 'Locked (after cutoff)'),
        ('baking', 'Baking'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    retailer = models.ForeignKey(
        Retailer,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    bakery = models.ForeignKey(
        Bakery,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    delivery_date = models.DateField(
        help_text='The date the bread will be delivered.'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    notes = models.CharField(max_length=300, blank=True)

    placed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-delivery_date', '-placed_at']
        unique_together = ('retailer', 'delivery_date')
        indexes = [
            models.Index(fields=['bakery', 'delivery_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'#{self.id} · {self.retailer.name} · {self.delivery_date}'

    def recalculate_total(self):
        total = sum(item.subtotal for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=['total_amount'])

    @property
    def is_locked(self):
        now = timezone.localtime()
        cutoff = self.bakery.cutoff_time
        cutoff_dt = timezone.make_aware(
            timezone.datetime.combine(
                self.delivery_date - timezone.timedelta(days=1),
                cutoff
            )
        )
        return now >= cutoff_dt

    @property
    def total_loaves(self):
        return sum(item.quantity for item in self.items.all())


# ============================================================
# ORDER ITEM
# ============================================================
class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text='Price snapshot at time of ordering.'
    )

    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        unique_together = ('order', 'product')

    def __str__(self):
        return f'{self.quantity} × {self.product.name}'

    @property
    def subtotal(self):
        return self.quantity * self.unit_price
