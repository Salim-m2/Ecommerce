from rest_framework import serializers
from .documents import Cart, CartItem


class CartItemSerializer(serializers.Serializer):
    """
    Read-only serializer for a single embedded CartItem.
    product_id is an ObjectId in MongoDB — we convert it to a plain string
    so the frontend never has to deal with BSON types.
    line_total is computed on-the-fly: price_at_add × quantity.
    """
    product_id   = serializers.SerializerMethodField()
    variant_id   = serializers.CharField()
    product_name = serializers.CharField()
    variant_sku  = serializers.CharField()
    color        = serializers.CharField(allow_null=True, required=False)
    size         = serializers.CharField(allow_null=True, required=False)
    image_url    = serializers.CharField(allow_null=True, required=False)
    price_at_add = serializers.FloatField()
    quantity     = serializers.IntegerField()
    line_total   = serializers.SerializerMethodField()

    def get_product_id(self, obj):
        return str(obj.product_id)

    def get_line_total(self, obj):
        return round(obj.price_at_add * obj.quantity, 2)


class CartSerializer(serializers.Serializer):
    """
    Full cart serializer.
    id is the MongoDB ObjectId converted to string.
    item_count is the sum of all quantities (not the number of distinct items).
    subtotal is the sum of all line totals.
    """
    id          = serializers.SerializerMethodField()
    items       = CartItemSerializer(many=True)
    item_count  = serializers.SerializerMethodField()
    subtotal    = serializers.SerializerMethodField()
    coupon_code = serializers.CharField(allow_null=True, required=False)
    updated_at  = serializers.DateTimeField()

    def get_id(self, obj):
        return str(obj.id)

    def get_item_count(self, obj):
        return obj.get_item_count()

    def get_subtotal(self, obj):
        return round(obj.get_subtotal(), 2)


class AddToCartSerializer(serializers.Serializer):
    """
    Validates the POST /cart/items/ request body.
    product_id and variant_id come in as plain strings from the frontend.
    The view is responsible for converting product_id to ObjectId and looking
    up the variant inside the product document.
    """
    product_id = serializers.CharField(required=True)
    variant_id = serializers.CharField(required=True)
    quantity   = serializers.IntegerField(default=1, min_value=1, max_value=100)


class UpdateCartItemSerializer(serializers.Serializer):
    """
    Validates the PATCH /cart/items/{index}/ request body.
    Only quantity can be changed — everything else is a snapshot.
    """
    quantity = serializers.IntegerField(required=True, min_value=1, max_value=100)