"""
MongoDB index creation for the products app.

IMPORTANT: Do NOT re-create indexes that mongoengine already creates automatically.
mongoengine creates an index for every field marked unique=True in the Document
definition. Attempting to create the same field with a different name causes
MongoDB error code 85 (IndexOptionsConflict).

Fields mongoengine auto-indexes (leave them out of this file):
  products.slug        ← unique=True on StringField → auto-creates "slug_1"
  categories.slug      ← unique=True on StringField → auto-creates "slug_1"
  categories.name      ← unique=True on StringField → auto-creates "name_1"

This file only creates the ADDITIONAL indexes that mongoengine does not
create automatically: compound indexes, sort indexes, and the text index.
"""
import logging

logger = logging.getLogger(__name__)


def _create_index(collection, keys, name, **kwargs):
    """
    Create a single index, logging a clear message on success or failure.
    Errors are caught per-index so one failure doesn't abort the rest.
    """
    try:
        collection.create_index(keys, name=name, **kwargs)
        logger.debug(f"   ✅ Index ensured: {name}")
    except Exception as e:
        # Code 85 = IndexOptionsConflict (already exists with a different name)
        # Code 86 = IndexKeySpecsConflict (same name, different keys)
        # Both are safe to skip — the underlying index still exists and works.
        error_code = getattr(e, 'code', None)
        if error_code in (85, 86):
            logger.debug(f"   ⏭  Index already exists, skipping: {name}")
        else:
            logger.error(f"   ❌ Failed to create index '{name}': {e}")


def create_product_indexes():
    """
    Ensure all ADDITIONAL MongoDB indexes exist for products and categories.
    Called from config/settings/base.py after mongoengine.connect().

    Safe to call on every startup — create_index() is idempotent for indexes
    that don't already exist, and _create_index() skips ones that do.
    """
    try:
        from apps.products.documents import Product, Category

        products_col  = Product._get_collection()
        categories_col = Category._get_collection()

        logger.info("Ensuring MongoDB product indexes...")

        # ── Products: compound + sort indexes ─────────────────────────────

        # Most listing page queries filter by both category AND is_active.
        # A compound index on both fields is significantly faster than two
        # separate single-field indexes for this combination.
        _create_index(
            products_col,
            [("category_id", 1), ("is_active", 1)],
            name="products_category_active",
        )

        # Price range queries: ?min_price=50&max_price=200
        _create_index(
            products_col,
            [("base_price", 1)],
            name="products_base_price",
        )

        # Sort by rating: ?sort=rating
        _create_index(
            products_col,
            [("avg_rating", -1)],
            name="products_avg_rating_desc",
        )

        # Sort by popularity: ?sort=popular
        _create_index(
            products_col,
            [("review_count", -1)],
            name="products_review_count_desc",
        )

        # Full-text search: ?search=jordan
        # MongoDB allows only ONE text index per collection.
        # Weights control relevance ranking: name matches outrank tag matches,
        # which outrank description matches.
        _create_index(
            products_col,
            [("name", "text"), ("description", "text"), ("tags", "text")],
            name="products_text_search",
            weights={"name": 10, "tags": 5, "description": 1},
        )

        # ── Categories: parent lookup ──────────────────────────────────────

        # Used when building the category tree: "fetch all children of parent X"
        # slug and name unique indexes are auto-created by mongoengine, skipped here.
        _create_index(
            categories_col,
            [("parent_id", 1)],
            name="categories_parent_id",
        )

        logger.info("✅ Product and Category MongoDB indexes ensured.")

    except Exception as e:
        # Catch-all for connection errors or import failures.
        # Log and continue — missing indexes degrade performance but don't break the app.
        logger.error(f"❌ Index setup failed entirely: {e}")