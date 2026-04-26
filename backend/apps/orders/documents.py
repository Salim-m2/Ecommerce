from mongoengine import (
    Document, EmbeddedDocument,
    StringField, ObjectIdField, FloatField, IntField,
    ListField, EmbeddedDocumentField, DateTimeField,
)
from datetime import datetime
from bson import ObjectId


class OrderItem(EmbeddedDocument):
    """
    Snapshot of the cart item at the moment of order creation.
    These fields NEVER change — even if the product is edited or deleted later.
    """
    product_id   = ObjectIdField(required=True)
    product_name = StringField(required=True)   # snapshot
    product_slug = StringField()                 # snapshot — for linking back to product page
    variant_id   = StringField(required=True)
    variant_sku  = StringField(required=True)    # snapshot
    color        = StringField()                 # snapshot
    size         = StringField()                 # snapshot
    image_url    = StringField()                 # snapshot
    quantity     = IntField(required=True, min_value=1)
    unit_price   = FloatField(required=True)     # price_at_add from cart — never recalculated
    subtotal     = FloatField(required=True)     # unit_price * quantity


class StatusHistory(EmbeddedDocument):
    """
    One entry per status change. Gives a full audit trail of the order lifecycle.
    """
    status     = StringField(required=True)
    changed_at = DateTimeField(default=datetime.utcnow)
    by         = StringField(default='system')  # 'system', 'admin', or user email
    note       = StringField()                  # optional admin note


class ShippingAddress(EmbeddedDocument):
    """
    Embedded — address is snapshotted at order time so changes to a user's
    saved addresses never retroactively affect old orders.
    """
    full_name   = StringField(required=True)
    phone       = StringField(required=True)
    street      = StringField(required=True)
    city        = StringField(required=True)
    country     = StringField(default='Kenya')
    postal_code = StringField()


class Order(Document):
    ORDER_STATUSES = [
        'pending', 'paid', 'processing',
        'shipped', 'delivered', 'cancelled', 'refunded',
    ]

    order_number     = StringField(required=True, unique=True)
    user_id          = ObjectIdField(required=True)
    status           = StringField(default='pending', choices=ORDER_STATUSES)
    items            = ListField(EmbeddedDocumentField(OrderItem))
    shipping_address = EmbeddedDocumentField(ShippingAddress)
    shipping_method  = StringField(default='standard')   # 'standard' or 'express'
    shipping_cost    = FloatField(default=0.0)
    subtotal         = FloatField(required=True)
    discount         = FloatField(default=0.0)
    tax              = FloatField(default=0.0)
    total            = FloatField(required=True)         # subtotal + shipping_cost - discount + tax
    coupon_code      = StringField()
    payment_id       = ObjectIdField()                   # ref to Payment._id, set after payment
    tracking_number  = StringField()
    notes            = StringField()
    status_history   = ListField(EmbeddedDocumentField(StatusHistory))
    created_at       = DateTimeField(default=datetime.utcnow)
    updated_at       = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'orders',
        'indexes': [
            {'fields': ['user_id', '-created_at']},
            {'fields': ['order_number'], 'unique': True},
        ],
    }

    def save(self, *args, **kwargs):
        # Always stamp updated_at on every save — no exceptions
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

    @classmethod
    def generate_order_number(cls):
        """
        Produces ORD-{YEAR}-{5-digit-zero-padded-count}.
        Example: ORD-2025-00001, ORD-2025-00142
        Counts only orders from the current calendar year so the count
        resets each January without collisions (unique index is the safety net).
        """
        year = datetime.utcnow().year
        count = cls.objects(order_number__startswith=f'ORD-{year}-').count() + 1
        return f'ORD-{year}-{str(count).zfill(5)}'

    @classmethod
    def create_from_cart(cls, cart, user_id, shipping_address, shipping_method, notes=''):
        """
        Converts a Cart into an Order.
        - Copies ALL snapshot fields from CartItem → OrderItem
        - Calculates subtotal, applies shipping cost, sets total
        - Saves and returns the new Order

        WHY we don't touch stock here:
        Stock is only decremented inside the Stripe webhook handler AFTER
        payment is confirmed (payment_intent.succeeded). This prevents stock
        being held for orders that are never paid.
        """
        shipping_cost = 5.0 if shipping_method == 'standard' else 15.0

        order_items = []
        subtotal = 0.0

        for cart_item in cart.items:
            item_subtotal = round(cart_item.price_at_add * cart_item.quantity, 2)
            subtotal += item_subtotal

            order_items.append(OrderItem(
                product_id   = cart_item.product_id,
                product_name = cart_item.product_name,
                product_slug = '',           # CartItem doesn't store slug; view can enrich this
                variant_id   = cart_item.variant_id,
                variant_sku  = cart_item.variant_sku,
                color        = cart_item.color,
                size         = cart_item.size,
                image_url    = cart_item.image_url,
                quantity     = cart_item.quantity,
                unit_price   = cart_item.price_at_add,
                subtotal     = item_subtotal,
            ))

        subtotal = round(subtotal, 2)
        total    = round(subtotal + shipping_cost, 2)

        order = cls(
            order_number     = cls.generate_order_number(),
            user_id          = ObjectId(str(user_id)),
            status           = 'pending',
            items            = order_items,
            shipping_address = shipping_address,
            shipping_method  = shipping_method,
            shipping_cost    = shipping_cost,
            subtotal         = subtotal,
            total            = total,
            notes            = notes or '',
            status_history   = [StatusHistory(status='pending', by='system')],
        )
        order.save()
        return order

    def add_status(self, status, by='system', note=''):
        """
        Updates the order status and appends an entry to status_history.
        Always call this instead of setting self.status directly —
        it keeps the audit trail intact.
        """
        self.status = status
        self.status_history.append(
            StatusHistory(status=status, by=by, note=note or '')
        )
        self.save()