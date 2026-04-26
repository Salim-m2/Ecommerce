from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from bson import ObjectId
from datetime import datetime

from apps.users.documents     import User
from apps.products.documents  import Product, Category
from apps.cart.documents      import Cart, CartItem
from apps.orders.documents    import Order, ShippingAddress
from apps.payments.documents  import Payment


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_user(email, role='customer'):
    u = User(
        email      = email,
        first_name = 'Test',
        last_name  = 'User',
        role       = role,
        is_active  = True,
    )
    u.set_password('testpass123')
    u.save()
    return u


def make_category():
    return Category(
        name = 'Test Category',
        slug = 'test-category',
    ).save()


def make_product(category, name='Test Product', price=100.0, stock=10):
    """
    Creates a simple product with one variant.
    Returns the saved Product document.
    """
    from apps.products.documents import Variant
    import uuid
    p = Product(
        seller_id   = ObjectId(),
        category_id = category.id,
        name        = name,
        slug        = name.lower().replace(' ', '-') + '-' + str(uuid.uuid4())[:8],
        description = 'Test description',
        base_price  = price,
        is_active   = True,
        variants    = [
            Variant(
                variant_id = str(uuid.uuid4()),
                sku        = f'SKU-{str(uuid.uuid4())[:8]}',
                price      = price,
                stock      = stock,
            )
        ],
    )
    p.save()
    return p


VALID_ADDRESS = {
    'full_name':   'John Kamau',
    'phone':       '+254712345678',
    'street':      '123 Kenyatta Avenue',
    'city':        'Nairobi',
    'country':     'Kenya',
    'postal_code': '00100',
}


# ── Test class ────────────────────────────────────────────────────────────────

class OrderAPITestCase(APITestCase):
    """
    Full test suite for order creation, listing, and detail retrieval.
    Adapted for IntaSend payment flow (no Stripe dependency).
    """

    def setUp(self):
        # Clean all collections before each test
        Order.objects.all().delete()
        Payment.objects.all().delete()
        Cart.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        User.objects.all().delete()

        # Create users
        self.customer  = make_user('customer@test.com', role='customer')
        self.customer2 = make_user('customer2@test.com', role='customer')
        self.seller    = make_user('seller@test.com', role='seller')

        # Create category and products
        self.category  = make_category()
        self.product_a = make_product(self.category, name='Product A', price=50.0,  stock=10)
        self.product_b = make_product(self.category, name='Product B', price=100.0, stock=5)

        # Shortcuts to the first variant of each product
        self.variant_a = self.product_a.variants[0]
        self.variant_b = self.product_b.variants[0]

        # Create a cart for the customer with 2 items
        cart, _ = Cart.get_or_create_for_user(self.customer.id)
        cart.items = [
            CartItem(
                product_id   = self.product_a.id,
                variant_id   = self.variant_a.variant_id,
                product_name = self.product_a.name,
                variant_sku  = self.variant_a.sku,
                price_at_add = self.variant_a.price,
                quantity     = 2,
                image_url    = '',
            ),
            CartItem(
                product_id   = self.product_b.id,
                variant_id   = self.variant_b.variant_id,
                product_name = self.product_b.name,
                variant_sku  = self.variant_b.sku,
                price_at_add = self.variant_b.price,
                quantity     = 1,
                image_url    = '',
            ),
        ]
        cart.save()
        self.cart = cart

        # Authenticated client for customer
        self.client = APIClient()
        self.client.force_authenticate(user=self.customer)

    def tearDown(self):
        Order.objects.all().delete()
        Payment.objects.all().delete()
        Cart.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        User.objects.all().delete()

    # ── Helper ────────────────────────────────────────────────────────────────

    def _create_order(self, shipping_method='standard', address=None):
        """Shortcut to create an order via the API."""
        return self.client.post('/api/v1/orders/', {
            'shipping_address': address or VALID_ADDRESS,
            'shipping_method':  shipping_method,
            'notes':            '',
        }, format='json')

    def _refill_cart(self):
        """
        Re-add items to the cart. Needed for tests that run after a
        successful order creation (which clears the cart).
        """
        cart = Cart.get_for_user(self.customer.id)
        cart.items = [
            CartItem(
                product_id   = self.product_a.id,
                variant_id   = self.variant_a.variant_id,
                product_name = self.product_a.name,
                variant_sku  = self.variant_a.sku,
                price_at_add = self.variant_a.price,
                quantity     = 2,
                image_url    = '',
            ),
        ]
        cart.save()

    # ── Order creation tests ──────────────────────────────────────────────────

    def test_create_order_success(self):
        """
        POST /orders/ with valid cart and address → 201.
        Response must include a valid order_number and status='pending'.
        Cart must be empty after creation.
        """
        response = self._create_order()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertTrue(data['order_number'].startswith('ORD-'))
        self.assertEqual(data['status'], 'pending')
        self.assertEqual(len(data['items']), 2)

        # Cart should be cleared
        cart = Cart.get_for_user(self.customer.id)
        self.assertEqual(len(cart.items), 0)

    def test_create_order_requires_authentication(self):
        """Unauthenticated POST → 401."""
        unauthenticated = APIClient()
        response = unauthenticated.post('/api/v1/orders/', {
            'shipping_address': VALID_ADDRESS,
            'shipping_method':  'standard',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_order_empty_cart_returns_400(self):
        """POST with an empty cart → 400 with informative message."""
        self.cart.items = []
        self.cart.save()

        response = self._create_order()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('empty', response.json()['detail'].lower())

    def test_create_order_insufficient_stock_returns_400(self):
        """
        If a cart item's variant has stock < quantity, order creation
        must be rejected before any order document is written.
        """
        # Set stock to 0 on product_a's variant
        self.product_a.variants[0].stock = 0
        self.product_a.save()

        response = self._create_order()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # No order should exist in the database
        self.assertEqual(Order.objects.count(), 0)

    def test_order_items_are_snapshots(self):
        """
        Order items must record the product name at creation time.
        Changing the product name afterwards must NOT affect the stored order.
        """
        response    = self._create_order()
        order_number = response.json()['order_number']
        original_name = self.product_a.name  # 'Product A'

        # Rename the product after the order was placed
        self.product_a.name = 'Renamed Product'
        self.product_a.save()

        # Fetch the order via API
        detail = self.client.get(f'/api/v1/orders/{order_number}/')
        items  = detail.json()['items']
        names  = [item['product_name'] for item in items]

        self.assertIn(original_name, names)          # snapshot preserved
        self.assertNotIn('Renamed Product', names)   # change not reflected

    def test_order_number_is_unique(self):
        """
        Two orders placed by the same user must have different order numbers.
        """
        r1 = self._create_order()
        self.assertEqual(r1.status_code, 201)

        self._refill_cart()
        r2 = self._create_order()
        self.assertEqual(r2.status_code, 201)

        self.assertNotEqual(
            r1.json()['order_number'],
            r2.json()['order_number'],
        )

    def test_shipping_cost_standard(self):
        """standard shipping → shipping_cost == 5.0"""
        response = self._create_order(shipping_method='standard')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['shipping_cost'], 5.0)

    def test_shipping_cost_express(self):
        """express shipping → shipping_cost == 15.0"""
        response = self._create_order(shipping_method='express')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['shipping_cost'], 15.0)

    def test_order_total_calculation(self):
        """
        total must equal subtotal + shipping_cost.
        With 2×$50 + 1×$100 = $200 subtotal + $5 standard = $205 total.
        """
        response = self._create_order(shipping_method='standard')
        self.assertEqual(response.status_code, 201)
        data = response.json()

        expected_subtotal = (2 * 50.0) + (1 * 100.0)   # 200.0
        expected_total    = expected_subtotal + 5.0      # 205.0

        self.assertAlmostEqual(data['subtotal'],      expected_subtotal, places=2)
        self.assertAlmostEqual(data['total'],         expected_total,    places=2)
        self.assertAlmostEqual(data['shipping_cost'], 5.0,               places=2)

    def test_missing_required_address_field_returns_400(self):
        """
        Shipping address missing a required field (city) → 400
        with a per-field validation error.
        """
        bad_address = {k: v for k, v in VALID_ADDRESS.items() if k != 'city'}
        response    = self._create_order(address=bad_address)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Order list / detail tests ─────────────────────────────────────────────

    def test_list_orders_returns_only_own_orders(self):
        """
        Customer A's order must NOT appear in customer B's order list.
        """
        # Customer creates an order
        self._create_order()

        # Customer B has an empty cart — create one with items
        cart_b, _ = Cart.get_or_create_for_user(self.customer2.id)
        cart_b.items = [
            CartItem(
                product_id   = self.product_a.id,
                variant_id   = self.variant_a.variant_id,
                product_name = self.product_a.name,
                variant_sku  = self.variant_a.sku,
                price_at_add = self.variant_a.price,
                quantity     = 1,
                image_url    = '',
            ),
        ]
        cart_b.save()

        client_b = APIClient()
        client_b.force_authenticate(user=self.customer2)
        client_b.post('/api/v1/orders/', {
            'shipping_address': VALID_ADDRESS,
            'shipping_method':  'standard',
        }, format='json')

        # Customer A sees only their own order
        response = self.client.get('/api/v1/orders/')
        self.assertEqual(response.status_code, 200)
        order_numbers = [o['order_number'] for o in response.json()['results']]
        self.assertEqual(len(order_numbers), 1)

        # Customer B sees only their own order
        response_b   = client_b.get('/api/v1/orders/')
        order_numbers_b = [o['order_number'] for o in response_b.json()['results']]
        self.assertEqual(len(order_numbers_b), 1)

        # The two order numbers must be different
        self.assertNotEqual(order_numbers[0], order_numbers_b[0])

    def test_get_order_detail_by_order_number(self):
        """
        GET /orders/{order_number}/ → 200 with full items, address, totals.
        """
        create_resp  = self._create_order()
        order_number = create_resp.json()['order_number']

        detail = self.client.get(f'/api/v1/orders/{order_number}/')
        self.assertEqual(detail.status_code, 200)

        data = detail.json()
        self.assertEqual(data['order_number'], order_number)
        self.assertEqual(len(data['items']), 2)
        self.assertIn('shipping_address', data)
        self.assertIn('total', data)

    def test_get_other_users_order_returns_404(self):
        """
        A user must not be able to fetch another user's order —
        even if they know the order number. Expect 404.
        """
        create_resp  = self._create_order()
        order_number = create_resp.json()['order_number']

        client_b = APIClient()
        client_b.force_authenticate(user=self.customer2)
        response = client_b.get(f'/api/v1/orders/{order_number}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_nonexistent_order_number_returns_404(self):
        """GET /orders/ORD-9999-99999/ → 404."""
        response = self.client.get('/api/v1/orders/ORD-9999-99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_orders_pagination(self):
        """
        Response shape must include count, total_pages, current_page, results.
        """
        self._create_order()
        response = self.client.get('/api/v1/orders/?page=1&page_size=5')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('count',        data)
        self.assertIn('total_pages',  data)
        self.assertIn('current_page', data)
        self.assertIn('results',      data)

    def test_unauthenticated_list_returns_401(self):
        """GET /orders/ without JWT cookie → 401."""
        response = APIClient().get('/api/v1/orders/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)