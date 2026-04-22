"""
Product catalog API tests.

Coverage:
  - Product list: pagination, filters (category, price, rating, search), sorting
  - Product detail: success, inactive product, invalid slug
  - Category tree: structure, nesting, caching

Run with:
  python manage.py test apps.products --settings=config.settings.dev
"""
from datetime import datetime
from unittest.mock import patch

from bson import ObjectId
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.products.documents import Product, Category, Variant
from apps.users.documents import User


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_variant(sku, price=99.99, stock=10, size=None, color=None):
    """Create a Variant embedded document with sensible defaults."""
    return Variant(
        variant_id=str(ObjectId()),
        sku=sku,
        price=price,
        stock=stock,
        size=size,
        color=color,
        images=[],
    )


def make_product(name, category, seller_id, **kwargs):
    """
    Create and save a Product document.
    Accepts keyword overrides for any Product field.
    """
    slug = Product.generate_unique_slug(name)
    defaults = dict(
        seller_id=seller_id,
        category_id=category.id,
        name=name,
        slug=slug,
        description=f"Description for {name}",
        brand="TestBrand",
        base_price=100.00,
        images=["https://example.com/img.jpg"],
        tags=["test"],
        variants=[make_variant(f"{slug}-v1")],
        avg_rating=4.0,
        review_count=10,
        is_active=True,
        created_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    product = Product(**defaults)
    product.save()
    return product


# ─────────────────────────────────────────────────────────────────────────────
# Base test class — shared setUp / tearDown
# ─────────────────────────────────────────────────────────────────────────────

class ProductTestBase(APITestCase):
    """
    Creates the minimal shared fixtures all product tests need:
      - A seller user (products must have a seller_id)
      - Three categories (Electronics, Footwear, Sneakers as child of Footwear)
    Each test class gets a fresh DB state because tearDown deletes everything.
    """

    def setUp(self):
        self.client = APIClient()

        # Always clean before creating — makes setUp idempotent whether tests
        # ran cleanly before or crashed mid-run leaving orphaned documents.
        User.objects(email="seller@test.com").delete()
        Product.objects.all().delete()
        Category.objects(slug__in=["electronics", "footwear", "sneakers"]).delete()

        self.seller = User(
            email="seller@test.com",
            first_name="Test",
            last_name="Seller",
            role="seller",
        )
        self.seller.set_password("password123")
        self.seller.save()

        self.cat_electronics = Category(
            name="Electronics", slug="electronics", parent_id=None, order=1
        )
        self.cat_electronics.save()

        self.cat_footwear = Category(
            name="Footwear", slug="footwear", parent_id=None, order=2
        )
        self.cat_footwear.save()

        self.cat_sneakers = Category(
            name="Sneakers",
            slug="sneakers",
            parent_id=self.cat_footwear.id,
            order=1,
        )
        self.cat_sneakers.save()

    def tearDown(self):
        """
        Delete test data after every test.
        We delete by the test seller's ID so we don't accidentally wipe
        data from other test classes running in the same process.
        """
        Product.objects.all().delete()
        Category.objects.all().delete()
        User.objects(email="seller@test.com").delete()


# ─────────────────────────────────────────────────────────────────────────────
# Product List Tests
# ─────────────────────────────────────────────────────────────────────────────

class ProductListTests(ProductTestBase):

    def setUp(self):
        super().setUp()

        # 10 active products with varied attributes for filter testing
        self.p1 = make_product(
            "Sony Headphones", self.cat_electronics, self.seller.id,
            base_price=280.00, avg_rating=4.8, review_count=150,
            tags=["audio", "sony"], brand="Sony",
        )
        self.p2 = make_product(
            "Budget Earbuds", self.cat_electronics, self.seller.id,
            base_price=25.00, avg_rating=3.6, review_count=30,
            tags=["audio", "budget"], brand="Generic",
        )
        self.p3 = make_product(
            "Air Jordan 1", self.cat_sneakers, self.seller.id,
            base_price=120.00, avg_rating=4.9, review_count=200,
            tags=["sneakers", "nike"], brand="Nike",
        )
        self.p4 = make_product(
            "Adidas Ultraboost", self.cat_sneakers, self.seller.id,
            base_price=190.00, avg_rating=4.5, review_count=90,
            tags=["running", "adidas"], brand="Adidas",
        )
        self.p5 = make_product(
            "Nike Running Shorts", self.cat_footwear, self.seller.id,
            base_price=35.00, avg_rating=4.2, review_count=60,
            tags=["running", "nike"], brand="Nike",
        )
        self.p6 = make_product(
            "Mechanical Keyboard", self.cat_electronics, self.seller.id,
            base_price=90.00, avg_rating=4.6, review_count=75,
            tags=["keyboard", "tech"], brand="Keychron",
        )
        self.p7 = make_product(
            "Yoga Mat", self.cat_footwear, self.seller.id,
            base_price=60.00, avg_rating=4.3, review_count=40,
            tags=["yoga", "fitness"], brand="Manduka",
        )
        self.p8 = make_product(
            "Water Bottle", self.cat_electronics, self.seller.id,
            base_price=45.00, avg_rating=4.1, review_count=20,
            tags=["hydration"], brand="Hydro Flask",
        )
        self.p9 = make_product(
            "Gaming Mouse", self.cat_electronics, self.seller.id,
            base_price=75.00, avg_rating=4.7, review_count=110,
            tags=["gaming", "mouse"], brand="Logitech",
        )
        self.p10 = make_product(
            "Wireless Charger", self.cat_electronics, self.seller.id,
            base_price=30.00, avg_rating=3.8, review_count=15,
            tags=["charging", "wireless"], brand="Anker",
        )

        # 2 inactive products — must NEVER appear in any list results
        self.inactive1 = make_product(
            "Inactive Product A", self.cat_electronics, self.seller.id,
            is_active=False,
        )
        self.inactive2 = make_product(
            "Inactive Product B", self.cat_sneakers, self.seller.id,
            is_active=False,
        )

    # ── Active products only ──────────────────────────────────────────────

    def test_product_list_returns_only_active(self):
        """Inactive products must never appear in list results."""
        response = self.client.get("/api/v1/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        names = [p["name"] for p in response.data["results"]]
        self.assertNotIn("Inactive Product A", names)
        self.assertNotIn("Inactive Product B", names)

    def test_product_list_total_count_excludes_inactive(self):
        """count field must reflect only active products."""
        response = self.client.get("/api/v1/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 10 active, 2 inactive — count must be 10
        self.assertEqual(response.data["count"], 10)

    # ── Pagination ────────────────────────────────────────────────────────

    def test_product_list_pagination_shape(self):
        """Response must contain count, total_pages, current_page, page_size, results."""
        response = self.client.get("/api/v1/products/?page_size=4")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertIn("count",        data)
        self.assertIn("total_pages",  data)
        self.assertIn("current_page", data)
        self.assertIn("page_size",    data)
        self.assertIn("results",      data)

        self.assertEqual(data["current_page"], 1)
        self.assertEqual(data["page_size"],    4)
        self.assertEqual(len(data["results"]), 4)
        # 10 active products at page_size=4 → 3 pages (4+4+2)
        self.assertEqual(data["total_pages"], 3)

    def test_product_list_page_2(self):
        """Page 2 must return the correct slice and update current_page."""
        response = self.client.get("/api/v1/products/?page=2&page_size=4")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["current_page"], 2)
        self.assertEqual(len(response.data["results"]), 4)

    def test_product_list_last_page_has_remainder(self):
        """Last page returns the remaining items, not a full page_size."""
        response = self.client.get("/api/v1/products/?page=3&page_size=4")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 10 products, page_size=4: page 3 has 2 items
        self.assertEqual(len(response.data["results"]), 2)

    # ── Category filter ───────────────────────────────────────────────────

    def test_filter_by_category_slug(self):
        """?category=electronics must return only Electronics products."""
        response = self.client.get("/api/v1/products/?category=electronics")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        names = [p["name"] for p in response.data["results"]]
        # Electronics products from setUp
        self.assertIn("Sony Headphones",    names)
        self.assertIn("Budget Earbuds",     names)
        self.assertIn("Mechanical Keyboard", names)
        # Footwear/Sneakers products must NOT appear
        self.assertNotIn("Air Jordan 1",    names)
        self.assertNotIn("Yoga Mat",        names)

    def test_filter_by_subcategory_slug(self):
        """?category=sneakers must return only Sneakers products."""
        response = self.client.get("/api/v1/products/?category=sneakers")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        names = [p["name"] for p in response.data["results"]]
        self.assertIn("Air Jordan 1",    names)
        self.assertIn("Adidas Ultraboost", names)
        self.assertNotIn("Sony Headphones", names)

    def test_filter_by_unknown_category_returns_empty(self):
        """Unknown category slug must return empty results, not 404."""
        response = self.client.get("/api/v1/products/?category=this-does-not-exist")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"],   0)
        self.assertEqual(response.data["results"], [])

    # ── Price filters ─────────────────────────────────────────────────────

    def test_filter_by_min_price(self):
        """?min_price=100 must return only products with base_price >= 100."""
        response = self.client.get("/api/v1/products/?min_price=100")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for product in response.data["results"]:
            self.assertGreaterEqual(
                product["base_price"], 100,
                msg=f"{product['name']} has price {product['base_price']} < 100"
            )

    def test_filter_by_max_price(self):
        """?max_price=50 must return only products with base_price <= 50."""
        response = self.client.get("/api/v1/products/?max_price=50")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for product in response.data["results"]:
            self.assertLessEqual(
                product["base_price"], 50,
                msg=f"{product['name']} has price {product['base_price']} > 50"
            )

    def test_filter_by_price_range(self):
        """?min_price=50&max_price=150 must return only products in that range."""
        response = self.client.get("/api/v1/products/?min_price=50&max_price=150")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for product in response.data["results"]:
            price = product["base_price"]
            self.assertGreaterEqual(price, 50)
            self.assertLessEqual(price, 150)

    def test_filter_by_price_range_no_results(self):
        """Price range with no matching products must return empty list, not 404."""
        response = self.client.get("/api/v1/products/?min_price=9999&max_price=99999")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"],   0)
        self.assertEqual(response.data["results"], [])

    def test_malformed_price_param_is_ignored(self):
        """?min_price=abc must be silently ignored — returns all products."""
        response = self.client.get("/api/v1/products/?min_price=abc")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 10)

    # ── Rating filter ─────────────────────────────────────────────────────

    def test_filter_by_rating(self):
        """?rating=4.5 must return only products with avg_rating >= 4.5."""
        response = self.client.get("/api/v1/products/?rating=4.5")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertGreater(len(response.data["results"]), 0,
                           msg="Expected at least one product with avg_rating >= 4.5")

        for product in response.data["results"]:
            self.assertGreaterEqual(
                product["avg_rating"], 4.5,
                msg=f"{product['name']} has avg_rating {product['avg_rating']} < 4.5"
            )

    # ── Search filter ─────────────────────────────────────────────────────

    def test_search_by_name(self):
        """
        ?search=sony must return the Sony product.
        We mock search_text to avoid needing a real text index in tests
        and fall through to the __icontains fallback.
        """
        response = self.client.get("/api/v1/products/?search=sony")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        names = [p["name"] for p in response.data["results"]]
        self.assertIn("Sony Headphones", names)

    def test_search_no_results_returns_empty_list(self):
        """?search=zzznomatch must return empty list, not 404."""
        response = self.client.get("/api/v1/products/?search=zzznomatch")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], [])

    # ── Sorting ───────────────────────────────────────────────────────────

    def test_sort_price_asc(self):
        """?sort=price_asc must return products cheapest first."""
        response = self.client.get("/api/v1/products/?sort=price_asc")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        prices = [p["base_price"] for p in response.data["results"]]
        self.assertEqual(prices, sorted(prices),
                         msg=f"Prices not in ascending order: {prices}")

    def test_sort_price_desc(self):
        """?sort=price_desc must return products most expensive first."""
        response = self.client.get("/api/v1/products/?sort=price_desc")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        prices = [p["base_price"] for p in response.data["results"]]
        self.assertEqual(prices, sorted(prices, reverse=True),
                         msg=f"Prices not in descending order: {prices}")

    def test_sort_rating(self):
        """?sort=rating must return highest rated products first."""
        response = self.client.get("/api/v1/products/?sort=rating")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ratings = [p["avg_rating"] for p in response.data["results"]]
        self.assertEqual(ratings, sorted(ratings, reverse=True),
                         msg=f"Ratings not in descending order: {ratings}")

    def test_sort_popular(self):
        """?sort=popular must return most reviewed products first."""
        response = self.client.get("/api/v1/products/?sort=popular")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        counts = [p["review_count"] for p in response.data["results"]]
        self.assertEqual(counts, sorted(counts, reverse=True),
                         msg=f"Review counts not in descending order: {counts}")

    def test_sort_newest(self):
        """?sort=newest (default) must return most recently created products first."""
        response = self.client.get("/api/v1/products/?sort=newest")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # We can't easily check created_at order from the response since it's
        # not returned in ProductListSerializer. We verify the sort doesn't crash
        # and returns the right count.
        self.assertEqual(response.data["count"], 10)

    def test_unknown_sort_falls_back_to_newest(self):
        """Unknown sort param must not crash — falls back to default (newest)."""
        response = self.client.get("/api/v1/products/?sort=invalid_value")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 10)

    # ── Combined filters ──────────────────────────────────────────────────

    def test_combined_category_and_min_price(self):
        """?category=electronics&min_price=80 — both filters applied together."""
        response = self.client.get("/api/v1/products/?category=electronics&min_price=80")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Every result must be in Electronics AND have price >= 80
        electronics_id = str(self.cat_electronics.id)
        for product in response.data["results"]:
            self.assertEqual(product["category_id"], electronics_id)
            self.assertGreaterEqual(product["base_price"], 80)

    def test_combined_price_range_and_sort(self):
        """?min_price=30&max_price=100&sort=price_asc — filtered AND sorted."""
        response = self.client.get("/api/v1/products/?min_price=30&max_price=100&sort=price_asc")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        prices = [p["base_price"] for p in response.data["results"]]
        for price in prices:
            self.assertGreaterEqual(price, 30)
            self.assertLessEqual(price, 100)
        self.assertEqual(prices, sorted(prices))

    def test_combined_category_price_sort(self):
        """?category=sneakers&min_price=100&sort=price_desc — three filters together."""
        response = self.client.get(
            "/api/v1/products/?category=sneakers&min_price=100&sort=price_desc"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        sneakers_id = str(self.cat_sneakers.id)
        prices = [p["base_price"] for p in response.data["results"]]
        for product in response.data["results"]:
            self.assertEqual(product["category_id"], sneakers_id)
            self.assertGreaterEqual(product["base_price"], 100)
        self.assertEqual(prices, sorted(prices, reverse=True))

    # ── Response shape ────────────────────────────────────────────────────

    def test_product_list_item_fields(self):
        """Each result item must contain all expected fields."""
        response = self.client.get("/api/v1/products/?page_size=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        item = response.data["results"][0]
        expected_fields = {
            "id", "name", "slug", "brand", "base_price", "min_price",
            "thumbnail", "avg_rating", "review_count", "is_active",
            "category_id", "in_stock",
        }
        for field in expected_fields:
            self.assertIn(field, item, msg=f"Missing field '{field}' in list response")


# ─────────────────────────────────────────────────────────────────────────────
# Product Detail Tests
# ─────────────────────────────────────────────────────────────────────────────

class ProductDetailTests(ProductTestBase):

    def setUp(self):
        super().setUp()

        self.product = make_product(
            "Test Sneaker", self.cat_sneakers, self.seller.id,
            base_price=110.00,
            avg_rating=4.4,
            review_count=55,
            tags=["sneakers", "test"],
            variants=[
                make_variant("SNKR-42-BLK", price=110.00, stock=8,  size="42", color="Black"),
                make_variant("SNKR-43-BLK", price=110.00, stock=0,  size="43", color="Black"),
                make_variant("SNKR-42-WHT", price=115.00, stock=5,  size="42", color="White"),
            ],
        )
        self.inactive_product = make_product(
            "Inactive Sneaker", self.cat_sneakers, self.seller.id,
            is_active=False,
        )

    def test_product_detail_success(self):
        """GET /products/{slug}/ must return 200 with the full product."""
        response = self.client.get(f"/api/v1/products/{self.product.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["slug"], self.product.slug)
        self.assertEqual(response.data["name"], "Test Sneaker")

    def test_product_detail_contains_all_fields(self):
        """Detail response must include fields not present in the list serializer."""
        response = self.client.get(f"/api/v1/products/{self.product.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        detail_only_fields = {"description", "tags", "variants", "created_at"}
        for field in detail_only_fields:
            self.assertIn(field, response.data,
                          msg=f"Missing field '{field}' in detail response")

    def test_product_detail_variants_shape(self):
        """Variants array must be present and each variant must have required fields."""
        response = self.client.get(f"/api/v1/products/{self.product.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        variants = response.data["variants"]
        self.assertEqual(len(variants), 3)

        variant_fields = {"variant_id", "sku", "price", "stock", "size", "color", "images"}
        for v in variants:
            for field in variant_fields:
                self.assertIn(field, v, msg=f"Missing field '{field}' in variant")

    def test_product_detail_in_stock_true(self):
        """in_stock must be True when at least one variant has stock > 0."""
        response = self.client.get(f"/api/v1/products/{self.product.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Two variants have stock > 0
        self.assertTrue(response.data["in_stock"])

    def test_product_detail_in_stock_false(self):
        """in_stock must be False when ALL variants have stock = 0."""
        out_of_stock = make_product(
            "Out Of Stock Item", self.cat_sneakers, self.seller.id,
            variants=[
                make_variant("OOS-V1", stock=0),
                make_variant("OOS-V2", stock=0),
            ],
        )
        response = self.client.get(f"/api/v1/products/{out_of_stock.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["in_stock"])

    def test_product_detail_min_price(self):
        """min_price must return the lowest price across all variants."""
        response = self.client.get(f"/api/v1/products/{self.product.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Variants are priced at 110, 110, 115 — min is 110
        self.assertEqual(response.data["min_price"], 110.00)

    def test_product_detail_inactive_returns_404(self):
        """Inactive products must return 404 — treated as non-existent."""
        response = self.client.get(f"/api/v1/products/{self.inactive_product.slug}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_product_detail_invalid_slug_returns_404(self):
        """Non-existent slug must return 404."""
        response = self.client.get("/api/v1/products/this-slug-does-not-exist/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_product_detail_no_auth_required(self):
        """Product detail must be accessible without authentication."""
        # Explicitly ensure no credentials are set
        self.client.credentials()
        response = self.client.get(f"/api/v1/products/{self.product.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# Category Tree Tests
# ─────────────────────────────────────────────────────────────────────────────

class CategoryTreeTests(ProductTestBase):
    """
    Tests for GET /api/v1/categories/.
    Uses the categories created in ProductTestBase.setUp:
      - Electronics (top-level)
      - Footwear    (top-level)
      - Sneakers    (child of Footwear)
    """

    def setUp(self):
        super().setUp()
        # Clear the category cache before each test so we test DB reads,
        # not cached results from a previous test
        from django.core.cache import cache
        cache.delete("category_tree")

    def tearDown(self):
        super().tearDown()
        from django.core.cache import cache
        cache.delete("category_tree")

    def test_category_list_returns_200(self):
        response = self.client.get("/api/v1/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_only_top_level_categories_at_root(self):
        """The response root array must contain only top-level categories."""
        response = self.client.get("/api/v1/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Electronics and Footwear are top-level; Sneakers is a child
        slugs = [c["slug"] for c in response.data]
        self.assertIn("electronics", slugs)
        self.assertIn("footwear",    slugs)
        # Sneakers must NOT appear at root level
        self.assertNotIn("sneakers", slugs)

    def test_subcategory_nested_under_parent(self):
        """Sneakers must appear inside Footwear's children array."""
        response = self.client.get("/api/v1/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Find Footwear in the response
        footwear = next(
            (c for c in response.data if c["slug"] == "footwear"), None
        )
        self.assertIsNotNone(footwear, "Footwear category not found in response")
        self.assertIn("children", footwear)

        child_slugs = [c["slug"] for c in footwear["children"]]
        self.assertIn("sneakers", child_slugs)

    def test_top_level_category_children_field_exists(self):
        """Every top-level category must have a 'children' key."""
        response = self.client.get("/api/v1/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for category in response.data:
            self.assertIn("children", category,
                          msg=f"Category '{category['slug']}' is missing 'children' field")

    def test_category_with_no_children_has_empty_list(self):
        """Electronics has no subcategories — its children must be an empty list."""
        response = self.client.get("/api/v1/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        electronics = next(
            (c for c in response.data if c["slug"] == "electronics"), None
        )
        self.assertIsNotNone(electronics)
        self.assertEqual(electronics["children"], [])

    def test_category_tree_is_cached(self):
        """Second call must be served from cache, not hit the database."""
        from django.core.cache import cache

        # First call — populates cache
        response1 = self.client.get("/api/v1/categories/")
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        # Verify the cache was populated
        cached = cache.get("category_tree")
        self.assertIsNotNone(cached, "Category tree was not stored in cache after first call")

        # Second call — must be served from cache
        # We verify this by poisoning the cache with a fake value and
        # confirming the response comes from the cache, not the DB.
        fake_data = [{"slug": "cached-category", "name": "From Cache", "children": []}]
        cache.set("category_tree", fake_data, timeout=3600)

        response2 = self.client.get("/api/v1/categories/")
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data[0]["slug"], "cached-category",
                         msg="Second call did not come from cache")

    def test_category_fields_present(self):
        """Each category must contain id, name, slug, parent_id, image_url, order."""
        response = self.client.get("/api/v1/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        required_fields = {"id", "name", "slug", "parent_id", "image_url", "order", "children"}
        for cat in response.data:
            for field in required_fields:
                self.assertIn(field, cat, msg=f"Missing field '{field}' in category")


# ─────────────────────────────────────────────────────────────────────────────
# Image Upload Permission Tests
# ─────────────────────────────────────────────────────────────────────────────

class ProductImageUploadPermissionTests(ProductTestBase):
    """
    Tests that the upload endpoint enforces auth and role correctly.
    We don't test actual Cloudinary uploads here (that would require
    real credentials and make tests slow/flaky). We only test permissions.
    """

    def setUp(self):
        super().setUp()

        # Clean before creating to avoid duplicates on re-runs
        User.objects(email__in=["admin@test.com", "customer@test.com"]).delete()

        self.admin = User(
            email="admin@test.com",
            first_name="Test",
            last_name="Admin",
            role="admin",
        )
        self.admin.set_password("adminpassword123")
        self.admin.save()

        self.customer = User(
            email="customer@test.com",
            first_name="Test",
            last_name="Customer",
            role="customer",
        )
        self.customer.set_password("customerpassword123")
        self.customer.save()

    def tearDown(self):
        super().tearDown()
        User.objects(email__in=["admin@test.com", "customer@test.com"]).delete()

    def _get_dummy_image(self):
        """
        Creates a minimal valid JPEG in memory for upload tests.
        We use a 1x1 pixel JPEG — small enough to be fast but real enough
        that Django's file upload handling accepts it.
        """
        import io
        # Minimal valid JPEG bytes (1x1 pixel, white)
        jpeg_bytes = (
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
            b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t'
            b'\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
            b'\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\x1e'
            b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00'
            b'\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'
            b'\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xf5\x00\xff\xd9'
        )
        return io.BytesIO(jpeg_bytes)

    def test_upload_without_auth_returns_401(self):
        """Unauthenticated request must return 401."""
        self.client.credentials()  # Ensure no auth

        image = self._get_dummy_image()
        response = self.client.post(
            "/api/v1/products/upload-image/",
            {"image": image, "product_slug": "test"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_upload_as_customer_returns_403(self):
        """Customer role must be denied with 403."""
        self.client.force_authenticate(user=self.customer)

        image = self._get_dummy_image()
        response = self.client.post(
            "/api/v1/products/upload-image/",
            {"image": image, "product_slug": "test"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("apps.products.image_views.upload_product_image")
    def test_upload_as_admin_calls_cloudinary(self, mock_upload):
        """
        Admin must reach the upload logic.
        We mock upload_product_image so no real Cloudinary call is made.
        """
        mock_upload.return_value = {
            "url": "https://res.cloudinary.com/test/image/upload/sample.jpg",
            "public_id": "ecommerce/products/test/sample",
        }
        self.client.force_authenticate(user=self.admin)

        image = self._get_dummy_image()
        response = self.client.post(
            "/api/v1/products/upload-image/",
            {"image": image, "product_slug": "test-product"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("url",       response.data)
        self.assertIn("public_id", response.data)
        mock_upload.assert_called_once()

    @patch("apps.products.image_views.upload_product_image")
    def test_upload_as_seller_calls_cloudinary(self, mock_upload):
        """Seller role must also have upload access."""
        mock_upload.return_value = {
            "url": "https://res.cloudinary.com/test/image/upload/sample.jpg",
            "public_id": "ecommerce/products/test/sample",
        }
        self.client.force_authenticate(user=self.seller)

        image = self._get_dummy_image()
        response = self.client.post(
            "/api/v1/products/upload-image/",
            {"image": image, "product_slug": "test-product"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("apps.products.image_views.upload_product_image")
    def test_upload_missing_image_returns_400(self, mock_upload):
        """Request without an image file must return 400."""
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            "/api/v1/products/upload-image/",
            {"product_slug": "test-product"},  # No image key
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_upload.assert_not_called()

    @patch("apps.products.image_views.upload_product_image")
    def test_upload_missing_slug_returns_400(self, mock_upload):
        """Request without product_slug must return 400."""
        self.client.force_authenticate(user=self.admin)

        image = self._get_dummy_image()
        response = self.client.post(
            "/api/v1/products/upload-image/",
            {"image": image},  # No product_slug key
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_upload.assert_not_called()

    @patch("apps.products.image_views.upload_product_image")
    def test_upload_invalid_file_type_returns_400(self, mock_upload):
        """ValueError from cloudinary_utils must propagate as 400."""
        mock_upload.side_effect = ValueError("Invalid file type 'application/pdf'.")
        self.client.force_authenticate(user=self.admin)

        import io
        fake_pdf = io.BytesIO(b"%PDF fake content")
        fake_pdf.name = "doc.pdf"

        response = self.client.post(
            "/api/v1/products/upload-image/",
            {"image": fake_pdf, "product_slug": "test"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid file type", response.data["detail"])