"""
Product serializers.

Two product serializers exist intentionally:
- ProductListSerializer: lightweight, used on listing/search pages. Returns minimal fields
  to keep paginated responses fast. Only the first image is returned.
- ProductDetailSerializer: full detail, used on the product page. Returns all images,
  all variants, description, and tags.

This split matters at scale — a page listing 48 products should not be serializing
full descriptions and variant arrays for every item.
"""
from rest_framework import serializers
from apps.products.documents import Product, Category, Variant


class VariantSerializer(serializers.Serializer):
    """
    Serializes an embedded Variant subdocument.
    Read-only — variants are managed through the product admin endpoints (Week 9).
    """
    variant_id = serializers.CharField(read_only=True)
    size       = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    color      = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    sku        = serializers.CharField()
    price      = serializers.FloatField()
    stock      = serializers.IntegerField()
    images     = serializers.ListField(child=serializers.CharField(), required=False)


class ProductListSerializer(serializers.Serializer):
    """
    Lightweight serializer for product grid / listing pages.
    Returns only what a ProductCard component needs to render.
    """
    id           = serializers.SerializerMethodField()
    name         = serializers.CharField()
    slug         = serializers.CharField()
    brand        = serializers.CharField(allow_null=True, allow_blank=True)
    base_price   = serializers.FloatField()
    min_price    = serializers.SerializerMethodField()
    thumbnail    = serializers.SerializerMethodField()  # First image only
    avg_rating   = serializers.FloatField()
    review_count = serializers.IntegerField()
    is_active    = serializers.BooleanField()
    category_id  = serializers.SerializerMethodField()
    in_stock     = serializers.SerializerMethodField()

    def get_id(self, obj):
        # mongoengine ObjectId must be converted to string for JSON serialization
        return str(obj.id)

    def get_category_id(self, obj):
        return str(obj.category_id) if obj.category_id else None

    def get_min_price(self, obj):
        """
        Returns the lowest price across all variants.
        This is what gets shown as the 'starting from' price on listing cards
        when variants have different prices (e.g. size-based pricing).
        """
        if not obj.variants:
            return obj.base_price
        prices = [v.price for v in obj.variants if v.price is not None]
        return min(prices) if prices else obj.base_price

    def get_thumbnail(self, obj):
        """
        Returns only the first image URL — listing pages don't need the full gallery.
        Returns None if the product has no images; the frontend renders a placeholder.
        """
        if obj.images:
            return obj.images[0]
        return None

    def get_in_stock(self, obj):
        """
        True if at least one variant has stock > 0.
        Used by ProductCard to show/hide the 'Out of Stock' badge.
        """
        if not obj.variants:
            return False
        return any(v.stock > 0 for v in obj.variants)


class ProductDetailSerializer(serializers.Serializer):
    """
    Full serializer for the product detail page.
    Extends the list fields with: description, all images, all variants, tags, timestamps.
    """
    id           = serializers.SerializerMethodField()
    name         = serializers.CharField()
    slug         = serializers.CharField()
    brand        = serializers.CharField(allow_null=True, allow_blank=True)
    description  = serializers.CharField()
    base_price   = serializers.FloatField()
    min_price    = serializers.SerializerMethodField()
    images       = serializers.ListField(child=serializers.CharField())
    tags         = serializers.ListField(child=serializers.CharField())
    variants     = VariantSerializer(many=True)
    avg_rating   = serializers.FloatField()
    review_count = serializers.IntegerField()
    is_active    = serializers.BooleanField()
    category_id  = serializers.SerializerMethodField()
    in_stock     = serializers.SerializerMethodField()
    created_at   = serializers.DateTimeField()

    def get_id(self, obj):
        return str(obj.id)

    def get_category_id(self, obj):
        return str(obj.category_id) if obj.category_id else None

    def get_min_price(self, obj):
        if not obj.variants:
            return obj.base_price
        prices = [v.price for v in obj.variants if v.price is not None]
        return min(prices) if prices else obj.base_price

    def get_in_stock(self, obj):
        if not obj.variants:
            return False
        return any(v.stock > 0 for v in obj.variants)


class CategorySerializer(serializers.Serializer):
    """
    Flat category serializer — used internally to build the tree.
    """
    id        = serializers.SerializerMethodField()
    name      = serializers.CharField()
    slug      = serializers.CharField()
    parent_id = serializers.SerializerMethodField()
    image_url = serializers.CharField(allow_null=True, allow_blank=True)
    order     = serializers.IntegerField()

    def get_id(self, obj):
        return str(obj.id)

    def get_parent_id(self, obj):
        return str(obj.parent_id) if obj.parent_id else None


class CategoryTreeSerializer(serializers.Serializer):
    """
    Nested category serializer — adds a 'children' list to each top-level category.
    The tree is built in CategoryListView in Python, not in the database,
    because our category count is small (< 100) and always fetched all at once.
    """
    id        = serializers.SerializerMethodField()
    name      = serializers.CharField()
    slug      = serializers.CharField()
    parent_id = serializers.SerializerMethodField()
    image_url = serializers.CharField(allow_null=True, allow_blank=True)
    order     = serializers.IntegerField()
    children  = serializers.SerializerMethodField()

    def get_id(self, obj):
        return str(obj.id)

    def get_parent_id(self, obj):
        return str(obj.parent_id) if obj.parent_id else None

    def get_children(self, obj):
        """
        The view attaches a '_children' attribute to each Category object
        before passing them to this serializer. We read it here.
        If not set (shouldn't happen), return an empty list.
        """
        children = getattr(obj, '_children', [])
        return CategorySerializer(children, many=True).data