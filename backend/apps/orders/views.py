import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from bson import ObjectId

from apps.orders.documents import Order, ShippingAddress
from apps.orders.serializers import (
    OrderSerializer,
    OrderListSerializer,
    CreateOrderSerializer,
)
from apps.cart.documents import Cart
from apps.products.documents import Product

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 10


def _validate_cart_stock(cart):
    """
    Checks every cart item against current product stock BEFORE creating
    an order. Returns a list of error strings for any items with
    insufficient stock. An empty list means all items are fine.

    WHY we check here AND in the webhook:
    - Here: prevents creating an unpayable order from the start
    - Webhook: atomically decrements stock only after confirmed payment,
      protecting against race conditions between concurrent orders
    """
    errors = []
    for item in cart.items:
        available = Product.objects(__raw__={
            '_id': item.product_id,
            'variants': {
                '$elemMatch': {
                    'variant_id': item.variant_id,
                    'stock':      {'$gte': item.quantity},
                }
            },
        }).first()

        if not available:
            errors.append(
                f'"{item.product_name}" ({item.variant_sku}) — '
                f'requested {item.quantity} but insufficient stock available.'
            )
    return errors


class OrderListCreateView(APIView):
    """
    GET  /api/v1/orders/  — list the authenticated user's orders (newest first)
    POST /api/v1/orders/  — create a new order from the user's cart
    """
    permission_classes = [IsAuthenticated]

    # ── GET: Order list ───────────────────────────────────────────────────────

    def get(self, request):
        try:
            page      = max(1, int(request.query_params.get('page', 1)))
            page_size = max(1, min(50, int(request.query_params.get('page_size', DEFAULT_PAGE_SIZE))))
        except (ValueError, TypeError):
            page      = 1
            page_size = DEFAULT_PAGE_SIZE

        user_oid = ObjectId(str(request.user.id))
        total    = Order.objects(user_id=user_oid).count()
        orders   = (
            Order.objects(user_id=user_oid)
            .order_by('-created_at')
            .skip((page - 1) * page_size)
            .limit(page_size)
        )

        serializer   = OrderListSerializer(orders, many=True)
        total_pages  = max(1, (total + page_size - 1) // page_size)

        return Response({
            'count':        total,
            'total_pages':  total_pages,
            'current_page': page,
            'page_size':    page_size,
            'results':      serializer.data,
        })

    # ── POST: Order create ────────────────────────────────────────────────────

    def post(self, request):
        # ── Step 1: Validate request body ────────────────────────────────
        serializer = CreateOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated        = serializer.validated_data
        shipping_method  = validated['shipping_method']
        notes            = validated.get('notes', '')
        address_data     = validated['shipping_address']

        # ── Step 2: Get the user's cart — reject if empty ─────────────────
        user_oid = ObjectId(str(request.user.id))
        cart     = Cart.get_for_user(user_oid)

        if not cart or not cart.items:
            return Response(
                {'detail': 'Your cart is empty. Add items before placing an order.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Step 3: Validate stock for every cart item ────────────────────
        # We check before creating the order so the user gets immediate
        # feedback. Stock is NOT decremented here — only after payment succeeds.
        stock_errors = _validate_cart_stock(cart)
        if stock_errors:
            return Response(
                {
                    'detail': 'Some items in your cart are no longer available.',
                    'items':  stock_errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Step 4: Build ShippingAddress EmbeddedDocument ───────────────
        shipping_address = ShippingAddress(
            full_name   = address_data['full_name'],
            phone       = address_data['phone'],
            street      = address_data['street'],
            city        = address_data['city'],
            country     = address_data.get('country', 'Kenya'),
            postal_code = address_data.get('postal_code', ''),
        )

        # ── Step 5: Create the Order from the cart ────────────────────────
        # create_from_cart() copies all snapshot fields (name, price, sku,
        # image) from CartItem → OrderItem so the order record is permanent
        # and self-contained, even if the product is edited or deleted later.
        try:
            order = Order.create_from_cart(
                cart             = cart,
                user_id          = user_oid,
                shipping_address = shipping_address,
                shipping_method  = shipping_method,
                notes            = notes,
            )
        except Exception as e:
            logger.error('Order creation failed for user %s: %s', str(request.user.id), str(e))
            return Response(
                {'detail': 'Could not create your order. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # ── Step 6: Clear the cart ────────────────────────────────────────
        # The cart has been converted into an order. We clear the items
        # now — not earlier — so that if order creation fails the user
        # still has their cart intact.
        cart.items = []
        cart.save()

        logger.info('Order %s created for user %s', order.order_number, str(request.user.id))

        # ── Step 7: Return 201 with the full order ────────────────────────
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class OrderDetailView(APIView):
    """
    GET /api/v1/orders/{order_number}/

    Returns the full order. Enforces ownership — returns 404 if the
    order_number exists but belongs to a different user. This prevents
    users from probing other users' order numbers.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):
        user_oid = ObjectId(str(request.user.id))
        order    = Order.objects(
            order_number = order_number,
            user_id      = user_oid,
        ).first()

        if not order:
            return Response(
                {'detail': 'Order not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(OrderSerializer(order).data)