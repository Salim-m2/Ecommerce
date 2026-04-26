from rest_framework import serializers
from apps.orders.documents import Order, OrderItem, ShippingAddress


class ShippingAddressSerializer(serializers.Serializer):
    """
    Used for both input validation (inside CreateOrderSerializer)
    and output rendering (nested inside OrderSerializer).
    """
    full_name   = serializers.CharField(required=True)
    phone       = serializers.CharField(required=True)
    street      = serializers.CharField(required=True)
    city        = serializers.CharField(required=True)
    country     = serializers.CharField(default='Kenya')
    postal_code = serializers.CharField(required=False, allow_blank=True, default='')


class OrderItemSerializer(serializers.Serializer):
    """
    Read-only. Renders a single embedded OrderItem.
    All fields are snapshots taken at order creation time — they never
    change even if the underlying product is edited or deleted.
    """
    product_id   = serializers.SerializerMethodField()
    product_name = serializers.CharField()
    product_slug = serializers.CharField()
    variant_id   = serializers.CharField()
    variant_sku  = serializers.CharField()
    color        = serializers.CharField()
    size         = serializers.CharField()
    image_url    = serializers.CharField()
    quantity     = serializers.IntegerField()
    unit_price   = serializers.FloatField()
    subtotal     = serializers.FloatField()

    def get_product_id(self, obj):
        # ObjectId must be cast to string — JSON cannot serialize ObjectId natively
        return str(obj.product_id) if obj.product_id else None


class OrderSerializer(serializers.Serializer):
    """
    Full read-only representation of an Order.
    Used for order detail and order confirmation pages.
    """
    id               = serializers.SerializerMethodField()
    order_number     = serializers.CharField()
    status           = serializers.CharField()
    items            = OrderItemSerializer(many=True)
    shipping_address = ShippingAddressSerializer()
    shipping_method  = serializers.CharField()
    shipping_cost    = serializers.FloatField()
    subtotal         = serializers.FloatField()
    discount         = serializers.FloatField()
    tax              = serializers.FloatField()
    total            = serializers.FloatField()
    coupon_code      = serializers.CharField(allow_null=True)
    tracking_number  = serializers.CharField(allow_null=True)
    notes            = serializers.CharField(allow_null=True)
    created_at       = serializers.DateTimeField()
    updated_at       = serializers.DateTimeField()

    def get_id(self, obj):
        return str(obj.id)


class OrderListSerializer(serializers.Serializer):
    """
    Lightweight read-only representation for the order history list.
    Avoids serializing all items — only the count and first image are needed
    for the list card UI.
    """
    id               = serializers.SerializerMethodField()
    order_number     = serializers.CharField()
    status           = serializers.CharField()
    total            = serializers.FloatField()
    item_count       = serializers.SerializerMethodField()
    first_item_image = serializers.SerializerMethodField()
    created_at       = serializers.DateTimeField()

    def get_id(self, obj):
        return str(obj.id)

    def get_item_count(self, obj):
        return len(obj.items)

    def get_first_item_image(self, obj):
        if obj.items:
            return obj.items[0].image_url
        return None


class CreateOrderSerializer(serializers.Serializer):
    """
    Validates the POST /orders/ request body.

    shipping_address is accepted as a raw dict and then validated
    by ShippingAddressSerializer internally. This lets us give precise
    per-field error messages rather than a single 'invalid' error.
    """
    shipping_address = serializers.DictField(required=True)
    shipping_method  = serializers.ChoiceField(
        choices=['standard', 'express'],
        default='standard',
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )

    def validate_shipping_address(self, value):
        """
        Run the address dict through ShippingAddressSerializer so every
        field gets its own validation error rather than a generic one.
        """
        address_serializer = ShippingAddressSerializer(data=value)
        if not address_serializer.is_valid():
            raise serializers.ValidationError(address_serializer.errors)
        return address_serializer.validated_data