"""
Product API views.

Endpoint summary:
  GET /api/v1/products/           ProductListView   — paginated list with filters
  GET /api/v1/products/{slug}/    ProductDetailView — full product + variants
  GET /api/v1/categories/         CategoryListView  — nested category tree (cached)
"""
import logging
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from apps.products.documents import Product, Category
from apps.products.serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    CategoryTreeSerializer,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Pagination helper
# ─────────────────────────────────────────────────────────────────────────────

def paginate_queryset(queryset, page, page_size):
    """
    Slices a mongoengine queryset and returns a dict with pagination metadata.

    Why manual pagination instead of DRF's PageNumberPagination?
    DRF's built-in pagination works with Django querysets. mongoengine returns
    its own queryset type, so we paginate manually with Python slicing — this
    is the standard pattern for mongoengine + DRF.

    Returns:
        {
            count:        total matching documents
            total_pages:  number of pages at this page_size
            current_page: the requested page number (1-indexed)
            page_size:    items per page
            results:      sliced list of documents for this page
        }
    """
    total_count = queryset.count()
    total_pages = max(1, -(-total_count // page_size))  # ceiling division

    # Clamp page to valid range
    page = max(1, min(page, total_pages))

    offset = (page - 1) * page_size
    results = list(queryset.skip(offset).limit(page_size))

    return {
        "count":        total_count,
        "total_pages":  total_pages,
        "current_page": page,
        "page_size":    page_size,
        "results":      results,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Views
# ─────────────────────────────────────────────────────────────────────────────

class ProductListView(APIView):
    """
    GET /api/v1/products/

    Supports query parameters:
      category   string  — category slug (e.g. "footwear", "sneakers")
      min_price  float   — minimum base_price
      max_price  float   — maximum base_price
      rating     float   — minimum avg_rating
      search     string  — MongoDB text search across name, description, tags
      sort       string  — newest (default) | price_asc | price_desc | rating | popular
      page       int     — page number, 1-indexed (default: 1)
      page_size  int     — items per page, max 48 (default: 12)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        params = request.query_params

        # ── Base queryset: only active products ───────────────────────────
        queryset = Product.objects(is_active=True)

        # ── Filter: category ──────────────────────────────────────────────
        category_slug = params.get("category", "").strip()
        if category_slug:
            category = Category.objects(slug=category_slug).first()
            if category:
                queryset = queryset.filter(category_id=category.id)
            else:
                # Unknown category slug → return empty results, not a 404.
                # The frontend filter sidebar shows category slugs from our own
                # API, but an external link might use a stale slug.
                return Response({
                    "count": 0,
                    "total_pages": 1,
                    "current_page": 1,
                    "page_size": 12,
                    "results": [],
                })

        # ── Filter: price range ───────────────────────────────────────────
        min_price = params.get("min_price", "").strip()
        max_price = params.get("max_price", "").strip()

        if min_price:
            try:
                queryset = queryset.filter(base_price__gte=float(min_price))
            except ValueError:
                pass  # Ignore malformed float — treat as no filter

        if max_price:
            try:
                queryset = queryset.filter(base_price__lte=float(max_price))
            except ValueError:
                pass

        # ── Filter: minimum rating ────────────────────────────────────────
        rating = params.get("rating", "").strip()
        if rating:
            try:
                queryset = queryset.filter(avg_rating__gte=float(rating))
            except ValueError:
                pass

       # ── Filter: text search ───────────────────────────────────────────
        # MongoDB $text search uses the text index on name + description + tags.
        # search_text() is LAZY — it builds a query object but doesn't hit
        # MongoDB until .count() or iteration. That means we can't catch
        # "text index required" errors here. Instead we store the search term
        # and handle fallback in a wrapper around paginate_queryset below.
        search = params.get("search", "").strip()
        if search:
            queryset = queryset.search_text(search)

        # ── Sort ──────────────────────────────────────────────────────────
        sort_map = {
            "newest":     "-created_at",
            "price_asc":  "base_price",
            "price_desc": "-base_price",
            "rating":     "-avg_rating",
            "popular":    "-review_count",
        }
        sort_param = params.get("sort", "newest")
        order_by = sort_map.get(sort_param, "-created_at")
        queryset = queryset.order_by(order_by)

        # ── Pagination ────────────────────────────────────────────────────
        try:
            page = max(1, int(params.get("page", 1)))
        except (ValueError, TypeError):
            page = 1

        try:
            page_size = min(48, max(1, int(params.get("page_size", 12))))
        except (ValueError, TypeError):
            page_size = 12

        # If the text index doesn't exist (e.g. on a fresh test database before
        # indexes are created), MongoDB raises OperationFailure code 27.
        # Fall back to a case-insensitive name contains search in that case.
        try:
            paginated = paginate_queryset(queryset, page, page_size)
        except Exception as e:
            from pymongo.errors import OperationFailure
            if isinstance(e, OperationFailure) and search:
                # Text index missing — fall back to icontains on name
                fallback_qs = Product.objects(is_active=True).filter(
                    name__icontains=search
                ).order_by(order_by)
                paginated = paginate_queryset(fallback_qs, page, page_size)
            else:
                raise

        # Serialize only the current page's results
        serializer = ProductListSerializer(paginated["results"], many=True)

        return Response({
            "count":        paginated["count"],
            "total_pages":  paginated["total_pages"],
            "current_page": paginated["current_page"],
            "page_size":    paginated["page_size"],
            "results":      serializer.data,
        })


class ProductDetailView(APIView):
    """
    GET /api/v1/products/{slug}/

    Returns the full product document including all variants.
    Returns 404 if not found OR if is_active=False — inactive products
    are treated as if they don't exist from the customer's perspective.
    """
    permission_classes = [AllowAny]

    def get(self, request, slug):
        product = Product.objects(slug=slug, is_active=True).first()

        if not product:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductDetailSerializer(product)
        return Response(serializer.data)


class CategoryListView(APIView):
    """
    GET /api/v1/categories/

    Returns the full category tree: top-level categories with their
    children nested inside a 'children' array.

    The tree is built in Python (not in MongoDB) because:
    - Our category count is small (< 100) — fetching all at once is fast
    - Building a tree in application code is more portable than $graphLookup
    - The result is cached for 1 hour, so this code runs rarely

    Cache key: 'category_tree'
    Cache TTL: 3600 seconds (1 hour)
    Note: In dev, Django uses in-memory cache by default. In Week 8 when
    Redis is wired up, this transparently switches to Redis with no code change.
    """
    permission_classes = [AllowAny]
    CACHE_KEY = "category_tree"
    CACHE_TTL = 3600  # 1 hour

    def get(self, request):
        # ── Try cache first ───────────────────────────────────────────────
        cached = cache.get(self.CACHE_KEY)
        if cached is not None:
            return Response(cached)

        # ── Build tree from DB ────────────────────────────────────────────
        all_categories = list(Category.objects.order_by("order", "name"))

        # Index all categories by their string ID for O(1) child lookup
        cat_by_id = {str(c.id): c for c in all_categories}

        # Attach an empty _children list to every category object
        for cat in all_categories:
            cat._children = []

        # Single pass: attach each category to its parent's _children list
        top_level = []
        for cat in all_categories:
            if cat.parent_id and str(cat.parent_id) in cat_by_id:
                parent = cat_by_id[str(cat.parent_id)]
                parent._children.append(cat)
            else:
                # parent_id is None or points to a non-existent category
                top_level.append(cat)

        # ── Serialize ─────────────────────────────────────────────────────
        serializer = CategoryTreeSerializer(top_level, many=True)
        result = serializer.data

        # ── Cache and return ──────────────────────────────────────────────
        cache.set(self.CACHE_KEY, result, timeout=self.CACHE_TTL)
        logger.debug(f"Category tree built from DB and cached ({len(top_level)} top-level).")

        return Response(result)