from datetime import datetime
from bson import ObjectId
import mongoengine as me


class CartItem(me.EmbeddedDocument):
    """
    Embedded inside Cart. Never a separate collection.
    Every field that could change on the product is SNAPSHOTTED here at add-time.
    This means editing a product later never corrupts existing carts.
    """
    product_id   = me.ObjectIdField(required=True)
    variant_id   = me.StringField(required=True)   # UUID string from Product.variants

    # --- Snapshot fields (frozen at the moment the item is added) ---
    product_name = me.StringField(required=True)
    variant_sku  = me.StringField(required=True)
    color        = me.StringField()                # optional — not all variants have color
    size         = me.StringField()                # optional — not all variants have size
    image_url    = me.StringField()                # first product image at add-time

    # price_at_add is THE price we will use at checkout — never recalculate from product
    price_at_add = me.FloatField(required=True)

    quantity     = me.IntField(required=True, min_value=1)


class Cart(me.Document):
    """
    One document per cart. Guests are identified by session_key (a UUID stored
    in the browser and sent as the X-Session-Key request header).
    Logged-in users are identified by user_id.
    After login, the guest cart is merged into the user cart and deleted.
    """
    user_id     = me.ObjectIdField(null=True)     # null = guest cart
    session_key = me.StringField(null=True)        # null = logged-in cart
    items       = me.ListField(me.EmbeddedDocumentField(CartItem))
    coupon_code = me.StringField(null=True)
    updated_at  = me.DateTimeField(default=datetime.utcnow)
    created_at  = me.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'carts',
    }
    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def save(self, *args, **kwargs):
        """Stamp updated_at on every save so we can clean up stale guest carts."""
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

    # ------------------------------------------------------------------
    # Class-level lookups
    # ------------------------------------------------------------------

    @classmethod
    def get_for_user(cls, user_id):
        """Return the cart for this user, or None."""
        return cls.objects(user_id=user_id).first()

    @classmethod
    def get_for_session(cls, session_key):
        """Return the guest cart for this session key, or None."""
        return cls.objects(session_key=session_key, user_id=None).first()

    @classmethod
    def get_or_create_for_user(cls, user_id):
        """
        Returns (cart, created). Gets the existing cart or creates an empty one.
        user_id can be a string or ObjectId — we normalize it here.
        """
        if not isinstance(user_id, ObjectId):
            user_id = ObjectId(str(user_id))
        cart = cls.get_for_user(user_id)
        if cart:
            return cart, False
        cart = cls(user_id=user_id)
        cart.save()
        return cart, True

    @classmethod
    def get_or_create_for_session(cls, session_key):
        """Returns (cart, created) for a guest session key."""
        cart = cls.get_for_session(session_key)
        if cart:
            return cart, False
        cart = cls(session_key=session_key)
        cart.save()
        return cart, True

    # ------------------------------------------------------------------
    # Instance helpers
    # ------------------------------------------------------------------

    def get_subtotal(self):
        """Sum of price_at_add * quantity for every item."""
        return sum(item.price_at_add * item.quantity for item in self.items)

    def get_item_count(self):
        """Total number of individual units across all items."""
        return sum(item.quantity for item in self.items)

    def find_item(self, product_id, variant_id):
        """
        Return the CartItem that matches both product_id AND variant_id, or None.
        product_id comparison normalises both sides to string to avoid ObjectId vs str mismatch.
        """
        pid_str = str(product_id)
        for item in self.items:
            if str(item.product_id) == pid_str and item.variant_id == variant_id:
                return item
        return None