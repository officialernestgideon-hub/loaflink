from decimal import Decimal
from orders.models import Product


CART_SESSION_KEY = 'shop_cart'   # {product_id_str: quantity_int}


class Cart:
    """
    Session-backed cart. Nothing is saved to the DB until checkout.
    """

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if cart is None:
            cart = {}
            self.session[CART_SESSION_KEY] = cart
        self.cart = cart

    # ---------- Mutators ----------
    def add(self, product, quantity=1, override=False):
        pid = str(product.id)
        if override:
            self.cart[pid] = int(quantity)
        else:
            self.cart[pid] = self.cart.get(pid, 0) + int(quantity)
        if self.cart[pid] <= 0:
            self.remove(product)
        self.save()

    def remove(self, product):
        pid = str(product.id)
        if pid in self.cart:
            del self.cart[pid]
            self.save()

    def clear(self):
        self.session[CART_SESSION_KEY] = {}
        self.save()

    def save(self):
        self.session.modified = True

    # ---------- Readers ----------
    def __len__(self):
        return sum(self.cart.values())

    def __iter__(self):
        """Yield each cart line with product object + subtotal."""
        product_ids = [int(pid) for pid in self.cart.keys()]
        products = Product.objects.filter(id__in=product_ids).select_related('bakery')
        product_map = {str(p.id): p for p in products}

        for pid, qty in self.cart.items():
            product = product_map.get(pid)
            if not product:
                continue
            yield {
                'product': product,
                'quantity': qty,
                'unit_price': product.price,
                'subtotal': product.price * qty,
            }

    def total(self):
        return sum(line['subtotal'] for line in self)

    def total_loaves(self):
        return sum(line['quantity'] for line in self)

    def is_empty(self):
        return len(self) == 0