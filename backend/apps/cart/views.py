from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from bson import ObjectId
from bson.errors import InvalidId

from apps.products.documents import Product
from .documents import Cart, CartItem
from .serializers import (
    CartSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
)


# ------------------------------------------------------------------ #
#  Helper — resolve the correct cart for this request
# ------------------------------------------------------------------ #

def get_cart_for_request(request):
    """
    Returns (cart, created) based on who is making the request.

    - Authenticated user  → cart identified by user._id
    - Guest with header   → cart identified by X-Session-Key header value
    - Guest, no header    → returns (None, False)
    """
    if request.user and request.user.is_authenticated:
        return Cart.get_or_create_for_user(request.user.id)

    session_key = request.META.get('HTTP_X_SESSION_KEY')
    if session_key:
        return Cart.get_or_create_for_session(session_key)

    return None, False


def empty_cart_response():
    """
    Returned when there is no cart at all (no session key, not authenticated).
    """
    return {
        'id': None,
        'items': [],
        'item_count': 0,
        'subtotal': 0.0,
        'coupon_code': None,
        'updated_at': None,
    }


# ------------------------------------------------------------------ #
#  GET /api/v1/cart/
# ------------------------------------------------------------------ #

class CartDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cart, _ = get_cart_for_request(request)

        if cart is None:
            return Response(empty_cart_response(), status=status.HTTP_200_OK)

        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


# ------------------------------------------------------------------ #
#  POST /api/v1/cart/items/
# ------------------------------------------------------------------ #

class CartItemAddView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        cart, _ = get_cart_for_request(request)
        if cart is None:
            return Response(
                {'detail': 'X-Session-Key header is required for guest cart.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AddToCartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product_id_str = serializer.validated_data['product_id']
        variant_id     = serializer.validated_data['variant_id']
        quantity       = serializer.validated_data['quantity']

        try:
            product_oid = ObjectId(product_id_str)
        except (InvalidId, TypeError):
            return Response(
                {'detail': 'Invalid product_id.'},
                status=status.HTTP_404_NOT_FOUND
            )

        product = Product.objects(id=product_oid, is_active=True).first()
        if not product:
            return Response(
                {'detail': 'Product not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        variant = next(
            (v for v in product.variants if v.variant_id == variant_id),
            None
        )
        if not variant:
            return Response(
                {'detail': 'Variant not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        existing_item = cart.find_item(product_oid, variant_id)
        new_quantity  = (existing_item.quantity + quantity) if existing_item else quantity

        stock_ok = Product.objects(__raw__={
            '_id': product_oid,
            'variants': {'$elemMatch': {
                'variant_id': variant_id,
                'stock': {'$gte': quantity}
            }}
        }).first()

        if not stock_ok:
            return Response(
                {'detail': 'Insufficient stock for the requested quantity.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if existing_item:
            existing_item.quantity = new_quantity
        else:
            image_url = product.images[0] if product.images else None
            new_item  = CartItem(
                product_id   = product_oid,
                variant_id   = variant_id,
                product_name = product.name,
                variant_sku  = variant.sku,
                color        = variant.color,
                size         = variant.size,
                image_url    = image_url,
                price_at_add = variant.price,
                quantity     = quantity,
            )
            cart.items.append(new_item)

        cart.save()
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


# ------------------------------------------------------------------ #
#  PATCH /api/v1/cart/items/{item_index}/
#  DELETE /api/v1/cart/items/{item_index}/
# ------------------------------------------------------------------ #

class CartItemDetailView(APIView):
    permission_classes = [AllowAny]

    def _get_cart_and_item(self, request, item_index):
        cart, _ = get_cart_for_request(request)
        if cart is None:
            return None, Response(
                {'detail': 'Cart not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if item_index < 0 or item_index >= len(cart.items):
            return None, Response(
                {'detail': 'Item index out of range.'},
                status=status.HTTP_404_NOT_FOUND
            )

        return cart, None

    def patch(self, request, item_index):
        cart, error = self._get_cart_and_item(request, item_index)
        if error:
            return error

        serializer = UpdateCartItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_quantity = serializer.validated_data['quantity']
        item         = cart.items[item_index]

        stock_ok = Product.objects(__raw__={
            '_id': item.product_id,
            'variants': {'$elemMatch': {
                'variant_id': item.variant_id,
                'stock': {'$gte': new_quantity}
            }}
        }).first()

        if not stock_ok:
            return Response(
                {'detail': 'Insufficient stock for the requested quantity.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart.items[item_index].quantity = new_quantity
        cart.save()
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)

    def delete(self, request, item_index):
        cart, error = self._get_cart_and_item(request, item_index)
        if error:
            return error

        cart.items.pop(item_index)
        cart.save()
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


# ------------------------------------------------------------------ #
#  POST /api/v1/cart/merge/
# ------------------------------------------------------------------ #

class CartMergeView(APIView):
    """
    Called by the frontend immediately after a successful login.
    Takes the guest cart identified by session_key and merges its
    items into the now-authenticated user's cart.

    Merge rules:
    - Same product+variant already in user cart → add quantities together,
      capped at available stock (no error thrown — we cap gracefully)
    - New product+variant → move the item directly into user cart
    - After merge the guest cart document is deleted from MongoDB
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_key = request.data.get('session_key')

        # No session key provided — nothing to merge, return user's cart
        if not session_key:
            user_cart, _ = Cart.get_or_create_for_user(request.user.id)
            return Response(CartSerializer(user_cart).data, status=status.HTTP_200_OK)

        # Find the guest cart
        guest_cart = Cart.get_for_session(session_key)

        # No guest cart found — return user's cart unchanged
        if not guest_cart:
            user_cart, _ = Cart.get_or_create_for_user(request.user.id)
            return Response(CartSerializer(user_cart).data, status=status.HTTP_200_OK)

        # Get or create the user's cart
        user_cart, _ = Cart.get_or_create_for_user(request.user.id)

        # Merge each guest item into the user cart
        for guest_item in guest_cart.items:
            existing = user_cart.find_item(guest_item.product_id, guest_item.variant_id)

            if existing:
                # Combine quantities but cap at available stock
                # We use the same atomic query pattern — if it returns None,
                # stock is less than the combined amount so we find the max
                # available stock and use that instead of throwing an error.
                combined = existing.quantity + guest_item.quantity

                stock_ok = Product.objects(
                    id=guest_item.product_id,
                    variants__variant_id=guest_item.variant_id,
                    variants__stock__gte=combined
                ).first()

                if stock_ok:
                    existing.quantity = combined
                else:
                    # Cap at whatever stock is actually available
                    product = Product.objects(id=guest_item.product_id).first()
                    if product:
                        variant = next(
                            (v for v in product.variants
                             if v.variant_id == guest_item.variant_id),
                            None
                        )
                        if variant and variant.stock > existing.quantity:
                            existing.quantity = variant.stock
                        # If user already has >= stock, leave quantity unchanged
            else:
                # Brand new item — move it directly into the user cart
                user_cart.items.append(guest_item)

        user_cart.save()

        # Delete the guest cart — it has been fully absorbed
        guest_cart.delete()

        return Response(CartSerializer(user_cart).data, status=status.HTTP_200_OK)


# ------------------------------------------------------------------ #
#  POST /api/v1/cart/coupon/
# ------------------------------------------------------------------ #

class CartCouponView(APIView):
    """
    Coupon validation skeleton.
    Real coupon logic is implemented in Week 10.
    This endpoint exists now so the frontend coupon input field
    can be wired up without errors.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        return Response(
            {'detail': 'Coupon support coming in Week 10.'},
            status=status.HTTP_200_OK
        )