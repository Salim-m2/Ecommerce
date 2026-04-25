import uuid
from bson import ObjectId
from rest_framework.test import APITestCase
from rest_framework import status

from apps.cart.documents import Cart, CartItem
from apps.products.documents import Product, Category, Variant
from apps.users.documents import User


class CartTestCase(APITestCase):

    SESSION_KEY = 'test-session-abc123'

    def setUp(self):
        Cart.objects.delete()
        Product.objects.delete()
        Category.objects.delete()
        User.objects.delete()

        self.category = Category(name='Test Category', slug='test-category', order=1)
        self.category.save()

        self.seller = User(email='seller@test.com', first_name='Seller', last_name='User', role='seller')
        self.seller.set_password('password123')
        self.seller.save()

        self.customer = User(email='customer@test.com', first_name='Customer', last_name='User', role='customer')
        self.customer.set_password('password123')
        self.customer.save()

        # ── Product A ─────────────────────────────────────────────────
        # variant_id is set explicitly — mongoengine's default= only fires
        # during DB write, but validation runs before that, so we must
        # provide the value ourselves in tests.
        self.va1_id = str(uuid.uuid4())
        self.va2_id = str(uuid.uuid4())

        self.product_a = Product(
            seller_id=self.seller.id,
            category_id=self.category.id,
            name='Product Alpha',
            slug='product-alpha',
            description='Test product alpha',
            base_price=50.00,
            is_active=True,
            variants=[
                Variant(variant_id=self.va1_id, size='M', color='Red',  sku='ALPHA-M-RED',  price=50.00, stock=10),
                Variant(variant_id=self.va2_id, size='L', color='Blue', sku='ALPHA-L-BLUE', price=60.00, stock=0),
            ],
        )
        self.product_a.save()
        self.product_a.reload()
        self.variant_a1 = self.product_a.variants[0]
        self.variant_a2 = self.product_a.variants[1]

        # ── Product B ─────────────────────────────────────────────────
        self.vb1_id = str(uuid.uuid4())
        self.vb2_id = str(uuid.uuid4())

        self.product_b = Product(
            seller_id=self.seller.id,
            category_id=self.category.id,
            name='Product Beta',
            slug='product-beta',
            description='Test product beta',
            base_price=100.00,
            is_active=True,
            variants=[
                Variant(variant_id=self.vb1_id, size='S',  color='Black', sku='BETA-S-BLK',  price=100.00, stock=5),
                Variant(variant_id=self.vb2_id, size='XL', color='White', sku='BETA-XL-WHT', price=120.00, stock=3),
            ],
        )
        self.product_b.save()
        self.product_b.reload()
        self.variant_b1 = self.product_b.variants[0]
        self.variant_b2 = self.product_b.variants[1]

        # ── Product C ─────────────────────────────────────────────────
        self.vc1_id = str(uuid.uuid4())

        self.product_c = Product(
            seller_id=self.seller.id,
            category_id=self.category.id,
            name='Product Charlie',
            slug='product-charlie',
            description='Test product charlie',
            base_price=25.00,
            is_active=True,
            variants=[
                Variant(variant_id=self.vc1_id, size='One Size', color='Green', sku='CHARLIE-OS-GRN', price=25.00, stock=1),
            ],
        )
        self.product_c.save()
        self.product_c.reload()
        self.variant_c1 = self.product_c.variants[0]

    def tearDown(self):
        Cart.objects.delete()
        Product.objects.delete()
        Category.objects.delete()
        User.objects.delete()

    # ── Guest cart tests ───────────────────────────────────────────────

    def test_get_empty_cart_no_session_key(self):
        response = self.client.get('/api/v1/cart/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['id'])
        self.assertEqual(response.data['items'], [])
        self.assertEqual(response.data['item_count'], 0)
        self.assertEqual(response.data['subtotal'], 0.0)

    def test_get_cart_with_session_key_creates_cart(self):
        response = self.client.get('/api/v1/cart/', HTTP_X_SESSION_KEY=self.SESSION_KEY)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['id'])
        self.assertEqual(response.data['items'], [])

    def test_add_item_as_guest(self):
        response = self.client.post(
            '/api/v1/cart/items/',
            data={'product_id': str(self.product_a.id), 'variant_id': self.variant_a1.variant_id, 'quantity': 1},
            format='json',
            HTTP_X_SESSION_KEY=self.SESSION_KEY,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['item_count'], 1)

    def test_add_item_snapshot_fields(self):
        self.client.post(
            '/api/v1/cart/items/',
            data={'product_id': str(self.product_a.id), 'variant_id': self.variant_a1.variant_id, 'quantity': 1},
            format='json',
            HTTP_X_SESSION_KEY=self.SESSION_KEY,
        )
        cart = Cart.get_for_session(self.SESSION_KEY)
        item = cart.items[0]
        self.assertEqual(item.product_name, 'Product Alpha')
        self.assertEqual(item.variant_sku,  'ALPHA-M-RED')
        self.assertEqual(item.price_at_add, 50.00)
        self.assertEqual(item.color, 'Red')
        self.assertEqual(item.size,  'M')

    def test_price_snapshot_not_affected_by_product_edit(self):
        self.client.post(
            '/api/v1/cart/items/',
            data={'product_id': str(self.product_a.id), 'variant_id': self.variant_a1.variant_id, 'quantity': 1},
            format='json',
            HTTP_X_SESSION_KEY=self.SESSION_KEY,
        )
        # Simulate seller changing the price
        self.product_a.variants[0].price = 999.00
        self.product_a.save()

        response = self.client.get('/api/v1/cart/', HTTP_X_SESSION_KEY=self.SESSION_KEY)
        self.assertEqual(response.data['items'][0]['price_at_add'], 50.00)

    def test_add_same_item_twice_merges_quantity(self):
        for _ in range(2):
            self.client.post(
                '/api/v1/cart/items/',
                data={'product_id': str(self.product_a.id), 'variant_id': self.variant_a1.variant_id, 'quantity': 1},
                format='json',
                HTTP_X_SESSION_KEY=self.SESSION_KEY,
            )
        response = self.client.get('/api/v1/cart/', HTTP_X_SESSION_KEY=self.SESSION_KEY)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['quantity'], 2)

    def test_add_item_exceeding_stock_returns_400(self):
        response = self.client.post(
            '/api/v1/cart/items/',
            data={'product_id': str(self.product_a.id), 'variant_id': self.variant_a1.variant_id, 'quantity': 9999},
            format='json',
            HTTP_X_SESSION_KEY=self.SESSION_KEY,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_out_of_stock_variant_returns_400(self):
        response = self.client.post(
            '/api/v1/cart/items/',
            data={'product_id': str(self.product_a.id), 'variant_id': self.variant_a2.variant_id, 'quantity': 1},
            format='json',
            HTTP_X_SESSION_KEY=self.SESSION_KEY,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_item_with_invalid_product_id_returns_404(self):
        response = self.client.post(
            '/api/v1/cart/items/',
            data={'product_id': str(ObjectId()), 'variant_id': 'fake-variant', 'quantity': 1},
            format='json',
            HTTP_X_SESSION_KEY=self.SESSION_KEY,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_item_with_invalid_variant_id_returns_404(self):
        response = self.client.post(
            '/api/v1/cart/items/',
            data={'product_id': str(self.product_a.id), 'variant_id': 'completely-fake-variant-id', 'quantity': 1},
            format='json',
            HTTP_X_SESSION_KEY=self.SESSION_KEY,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_item_quantity(self):
        self.client.post(
            '/api/v1/cart/items/',
            data={'product_id': str(self.product_a.id), 'variant_id': self.variant_a1.variant_id, 'quantity': 1},
            format='json',
            HTTP_X_SESSION_KEY=self.SESSION_KEY,
        )
        response = self.client.patch(
            '/api/v1/cart/items/0/',
            data={'quantity': 3},
            format='json',
            HTTP_X_SESSION_KEY=self.SESSION_KEY,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items'][0]['quantity'], 3)

    def test_update_item_quantity_exceeds_stock_returns_400(self):
        self.client.post(
            '/api/v1/cart/items/',
            data={'product_id': str(self.product_a.id), 'variant_id': self.variant_a1.variant_id, 'quantity': 1},
            format='json',
            HTTP_X_SESSION_KEY=self.SESSION_KEY,
        )
        response = self.client.patch(
            '/api/v1/cart/items/0/',
            data={'quantity': 9999},
            format='json',
            HTTP_X_SESSION_KEY=self.SESSION_KEY,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_item(self):
        self.client.post(
            '/api/v1/cart/items/',
            data={'product_id': str(self.product_a.id), 'variant_id': self.variant_a1.variant_id, 'quantity': 1},
            format='json',
            HTTP_X_SESSION_KEY=self.SESSION_KEY,
        )
        response = self.client.delete('/api/v1/cart/items/0/', HTTP_X_SESSION_KEY=self.SESSION_KEY)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items'], [])

    def test_delete_invalid_index_returns_404(self):
        response = self.client.delete('/api/v1/cart/items/999/', HTTP_X_SESSION_KEY=self.SESSION_KEY)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cart_subtotal_calculation(self):
        self.client.post(
            '/api/v1/cart/items/',
            data={'product_id': str(self.product_a.id), 'variant_id': self.variant_a1.variant_id, 'quantity': 2},
            format='json',
            HTTP_X_SESSION_KEY=self.SESSION_KEY,
        )
        self.client.post(
            '/api/v1/cart/items/',
            data={'product_id': str(self.product_b.id), 'variant_id': self.variant_b1.variant_id, 'quantity': 1},
            format='json',
            HTTP_X_SESSION_KEY=self.SESSION_KEY,
        )
        response = self.client.get('/api/v1/cart/', HTTP_X_SESSION_KEY=self.SESSION_KEY)
        # (50.00 × 2) + (100.00 × 1) = 200.00
        self.assertEqual(response.data['subtotal'], 200.00)

    def test_item_count(self):
        self.client.post(
            '/api/v1/cart/items/',
            data={'product_id': str(self.product_a.id), 'variant_id': self.variant_a1.variant_id, 'quantity': 2},
            format='json',
            HTTP_X_SESSION_KEY=self.SESSION_KEY,
        )
        self.client.post(
            '/api/v1/cart/items/',
            data={'product_id': str(self.product_b.id), 'variant_id': self.variant_b1.variant_id, 'quantity': 3},
            format='json',
            HTTP_X_SESSION_KEY=self.SESSION_KEY,
        )
        response = self.client.get('/api/v1/cart/', HTTP_X_SESSION_KEY=self.SESSION_KEY)
        self.assertEqual(response.data['item_count'], 5)

    # ── Authenticated cart tests ───────────────────────────────────────

    def test_get_cart_authenticated(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.get('/api/v1/cart/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items'], [])

    def test_add_item_authenticated(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.post(
            '/api/v1/cart/items/',
            data={'product_id': str(self.product_a.id), 'variant_id': self.variant_a1.variant_id, 'quantity': 1},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)

    def test_guest_and_user_carts_are_separate(self):
        self.client.post(
            '/api/v1/cart/items/',
            data={'product_id': str(self.product_a.id), 'variant_id': self.variant_a1.variant_id, 'quantity': 1},
            format='json',
            HTTP_X_SESSION_KEY=self.SESSION_KEY,
        )
        self.client.force_authenticate(user=self.customer)
        self.client.post(
            '/api/v1/cart/items/',
            data={'product_id': str(self.product_b.id), 'variant_id': self.variant_b1.variant_id, 'quantity': 1},
            format='json',
        )
        response = self.client.get('/api/v1/cart/')
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['product_name'], 'Product Beta')

    # ── Cart merge tests ───────────────────────────────────────────────

    def test_merge_guest_cart_into_user_cart(self):
        self.client.post(
            '/api/v1/cart/items/',
            data={'product_id': str(self.product_a.id), 'variant_id': self.variant_a1.variant_id, 'quantity': 2},
            format='json',
            HTTP_X_SESSION_KEY=self.SESSION_KEY,
        )
        self.client.force_authenticate(user=self.customer)
        response = self.client.post(
            '/api/v1/cart/merge/',
            data={'session_key': self.SESSION_KEY},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['quantity'], 2)

    def test_merge_combines_duplicate_items(self):
        self.client.post(
            '/api/v1/cart/items/',
            data={'product_id': str(self.product_a.id), 'variant_id': self.variant_a1.variant_id, 'quantity': 2},
            format='json',
            HTTP_X_SESSION_KEY=self.SESSION_KEY,
        )
        self.client.force_authenticate(user=self.customer)
        self.client.post(
            '/api/v1/cart/items/',
            data={'product_id': str(self.product_a.id), 'variant_id': self.variant_a1.variant_id, 'quantity': 3},
            format='json',
        )
        response = self.client.post(
            '/api/v1/cart/merge/',
            data={'session_key': self.SESSION_KEY},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['quantity'], 5)

    def test_merge_with_no_guest_cart(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.post(
            '/api/v1/cart/merge/',
            data={'session_key': 'nonexistent-session-key'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items'], [])

    def test_merge_deletes_guest_cart(self):
        self.client.post(
            '/api/v1/cart/items/',
            data={'product_id': str(self.product_a.id), 'variant_id': self.variant_a1.variant_id, 'quantity': 1},
            format='json',
            HTTP_X_SESSION_KEY=self.SESSION_KEY,
        )
        self.client.force_authenticate(user=self.customer)
        self.client.post('/api/v1/cart/merge/', data={'session_key': self.SESSION_KEY}, format='json')
        self.assertIsNone(Cart.get_for_session(self.SESSION_KEY))

    def test_merge_requires_authentication(self):
        response = self.client.post(
            '/api/v1/cart/merge/',
            data={'session_key': self.SESSION_KEY},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_merge_respects_stock_limit(self):
        # Guest: qty=8, User: qty=5, stock=10 → merged should be capped at 10
        self.client.post(
            '/api/v1/cart/items/',
            data={'product_id': str(self.product_a.id), 'variant_id': self.variant_a1.variant_id, 'quantity': 8},
            format='json',
            HTTP_X_SESSION_KEY=self.SESSION_KEY,
        )
        self.client.force_authenticate(user=self.customer)
        self.client.post(
            '/api/v1/cart/items/',
            data={'product_id': str(self.product_a.id), 'variant_id': self.variant_a1.variant_id, 'quantity': 5},
            format='json',
        )
        response = self.client.post(
            '/api/v1/cart/merge/',
            data={'session_key': self.SESSION_KEY},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items'][0]['quantity'], 10)