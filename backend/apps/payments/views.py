import logging

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from bson import ObjectId, errors as bson_errors
from intasend import APIService

from apps.orders.documents import Order
from apps.payments.documents import Payment
from apps.products.documents import Product

logger = logging.getLogger(__name__)


def _get_intasend_service():
    """
    Returns a configured IntaSend APIService instance.
    Reads test mode from settings so the same code works in both
    sandbox (INTASEND_TEST_MODE=True) and production (False).
    """
    return APIService(
        token           = settings.INTASEND_API_TOKEN,
        publishable_key = settings.INTASEND_PUBLISHABLE_KEY,
        test            = settings.INTASEND_TEST_MODE,
    )


def _decrement_stock(order):
    """
    Atomically decrements product variant stock for every order item.

    Uses MongoDB's positional operator with an $elemMatch filter that
    includes stock >= quantity — so the decrement only fires if stock
    is still sufficient at write time. Two concurrent webhooks for the
    same order cannot produce negative stock.
    """
    for item in order.items:
        result = Product.objects(__raw__={
            '_id': item.product_id,
            'variants': {
                '$elemMatch': {
                    'variant_id': item.variant_id,
                    'stock':      {'$gte': item.quantity},
                }
            },
        }).update_one(__raw__={
            '$inc': {'variants.$.stock': -item.quantity}
        })

        if result == 0:
            logger.warning(
                'Stock shortfall on paid order %s: product_id=%s variant_id=%s qty=%d',
                order.order_number,
                str(item.product_id),
                item.variant_id,
                item.quantity,
            )


def _fulfill_order(payment, invoice_id):
    """
    Marks Payment as succeeded and Order as paid, then decrements stock.

    Shared by VerifyPaymentView and IntaSendWebhookView so fulfillment
    logic is never duplicated.

    Idempotent: if the payment is already succeeded we return immediately
    without touching the order or stock a second time.
    """
    if payment.status == 'succeeded':
        logger.info(
            '_fulfill_order: payment %s already succeeded — skipping duplicate call',
            str(payment.id),
        )
        return

    payment.intasend_invoice_id = str(invoice_id)
    payment.status = 'succeeded'
    payment.save()

    order = Order.objects(id=payment.order_id).first()
    if not order:
        logger.error('_fulfill_order: Order not found for payment %s', str(payment.id))
        return

    if order.status != 'pending':
        logger.info(
            '_fulfill_order: order %s already has status=%s — skipping status update',
            order.order_number, order.status,
        )
        return

    order.add_status('paid', by='intasend')
    _decrement_stock(order)
    logger.info('Order %s fulfilled successfully', order.order_number)


# ── View 1: Initialize Payment ────────────────────────────────────────────────

class InitializePaymentView(APIView):
    """
    POST /api/v1/payments/initialize/
    Body: { "order_id": "<string>" }

    Creates an IntaSend hosted checkout session and returns the payment URL.
    The frontend redirects the user to this URL to complete payment.

    Flow:
      Frontend POSTs here
      → we call IntaSend SDK
      → IntaSend returns a hosted checkout URL
      → frontend does window.location.href = payment_url
      → user pays on IntaSend's hosted page (M-Pesa, card, etc.)
      → IntaSend redirects back to /order-confirmation/{order_number}
        with ?checkout_id=...&invoice_id=...&order_tracking_id=... appended
      → frontend reads those URL params and calls VerifyPaymentView
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id_str = request.data.get('order_id', '').strip()

        if not order_id_str:
            return Response({'detail': 'order_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order_oid = ObjectId(order_id_str)
        except (bson_errors.InvalidId, TypeError):
            return Response({'detail': 'Invalid order_id format.'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify the order exists AND belongs to the authenticated user
        order = Order.objects(id=order_oid, user_id=request.user.id).first()
        if not order:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        if order.status != 'pending':
            return Response(
                {'detail': f'Order cannot be paid. Current status: {order.status}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Idempotency ───────────────────────────────────────────────────
        # If a pending Payment already exists for this order, create a fresh
        # checkout session with the same api_ref so IntaSend can link them.
        existing_payment = Payment.objects(order_id=order.id, status='pending').first()

        # ── Get user details for the checkout form ────────────────────────
        from apps.users.documents import User as UserDoc
        user_doc = UserDoc.objects(id=request.user.id).first()

        email      = user_doc.email      if user_doc else 'customer@store.com'
        first_name = user_doc.first_name if user_doc else 'Customer'
        last_name  = user_doc.last_name  if user_doc else ''
        phone      = user_doc.phone      if user_doc else ''

        # redirect_url is where IntaSend sends the user AFTER payment.
        # We include order_number so the confirmation page knows which
        # order to show — IntaSend will append its own params to this URL.
        redirect_url = (
            f"{settings.FRONTEND_URL}/order-confirmation/{order.order_number}"
        )

        # ── Create IntaSend checkout session ──────────────────────────────
        try:
            service  = _get_intasend_service()
            response = service.collect.checkout(
                phone_number = phone.replace('+', '') if phone else '',
                email        = email,
                first_name   = first_name,
                last_name    = last_name,
                amount       = order.total,
                currency     = 'KES',
                comment      = f'Payment for order {order.order_number}',
                redirect_url = redirect_url,
                api_ref      = order.order_number,   # our reference — comes back in webhook
            )
        except Exception as e:
            logger.error('IntaSend checkout creation error: %s', str(e))
            return Response(
                {'detail': 'Payment provider error. Please try again.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        payment_url       = response.get('url')
        checkout_id       = response.get('id')     # UUID assigned by IntaSend

        if not payment_url or not checkout_id:
            logger.error('IntaSend returned unexpected response: %s', response)
            return Response(
                {'detail': 'Could not initialize payment. Please try again.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # ── Persist Payment document ──────────────────────────────────────
        if existing_payment:
            # Update the checkout_id in case a new session was created
            existing_payment.intasend_checkout_id = checkout_id
            existing_payment.save()
        else:
            payment = Payment(
                order_id             = order.id,
                api_ref              = order.order_number,
                intasend_checkout_id = checkout_id,
                amount               = order.total,
                currency             = 'KES',
                status               = 'pending',
            )
            payment.save()

            # Link Payment back to Order for traceability
            order.payment_id = payment.id
            order.save()

        return Response({
            'payment_url':  payment_url,
            'checkout_id':  checkout_id,
            'order_number': order.order_number,
        })


# ── View 2: Verify Payment (called after IntaSend redirect) ───────────────────

class VerifyPaymentView(APIView):
    """
    POST /api/v1/payments/verify/
    Body: { "checkout_id": "uuid", "invoice_id": "NR5XKGY" }

    Called by the frontend after IntaSend redirects the user back.
    IntaSend appends ?checkout_id=...&invoice_id=...&order_tracking_id=...
    to the redirect URL. The frontend reads these and POSTs them here.

    WHY server-side verification:
    We NEVER trust the redirect URL params alone — they can be tampered with.
    We always re-verify directly with IntaSend's API using our secret token
    before marking any order as paid.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        checkout_id = request.data.get('checkout_id', '').strip()
        invoice_id  = request.data.get('invoice_id', '').strip()

        if not checkout_id or not invoice_id:
            return Response(
                {'detail': 'checkout_id and invoice_id are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Find our Payment document by the checkout_id IntaSend assigned
        payment = Payment.objects(intasend_checkout_id=checkout_id).first()
        if not payment:
            return Response({'detail': 'Payment record not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Verify ownership — the order must belong to the authenticated user
        order = Order.objects(id=payment.order_id, user_id=request.user.id).first()
        if not order:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Already succeeded — webhook may have beaten the redirect. Return success.
        if payment.status == 'succeeded':
            return Response({'status': 'COMPLETE', 'order_number': order.order_number})

        # ── Verify with IntaSend ──────────────────────────────────────────
        # service.collect.status() calls GET /api/v1/payment-invoices/{invoice_id}/
        # and returns the current invoice state from IntaSend's servers.
        try:
            service  = _get_intasend_service()
            result   = service.collect.status(invoice_id=invoice_id)
        except Exception as e:
            logger.error('IntaSend status check error: %s', str(e))
            return Response(
                {'detail': 'Verification failed. Please contact support.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # IntaSend invoice states: PENDING, PROCESSING, COMPLETE, FAILED
        invoice_state = result.get('invoice', {}).get('state', '')

        logger.info(
            'IntaSend verify: checkout_id=%s invoice_id=%s state=%s',
            checkout_id, invoice_id, invoice_state,
        )

        if invoice_state == 'COMPLETE':
            _fulfill_order(payment, invoice_id)
            return Response({'status': 'COMPLETE', 'order_number': order.order_number})

        if invoice_state in ('FAILED', 'CANCELLED'):
            payment.status = 'failed'
            payment.save()
            return Response(
                {'status': invoice_state, 'detail': 'Payment was not completed.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # PENDING or PROCESSING — payment is still in progress
        return Response({'status': invoice_state, 'detail': 'Payment is still processing.'})


# ── View 3: Webhook (IntaSend pushes events here) ─────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class IntaSendWebhookView(APIView):
    """
    POST /api/v1/payments/webhook/?secret=INTASEND_WEBHOOK_SECRET

    Receives real-time payment notifications pushed by IntaSend.
    This is the ONLY endpoint exempt from JWT auth.

    Security:
    IntaSend does not HMAC-sign its webhook payloads. Instead, we embed
    a secret in the webhook URL itself (configured in IntaSend dashboard).
    We check this secret on every request.

    IMPORTANT — this is a backup/fallback to VerifyPaymentView:
    In the happy path the user is redirected back and VerifyPaymentView
    fulfills the order. The webhook handles cases where the user closes
    the browser before being redirected, or the redirect silently fails.

    Because both paths call _fulfill_order(), and _fulfill_order() is
    idempotent, it is safe for both to run — the second is a no-op.
    """
    authentication_classes = []
    permission_classes     = [AllowAny]

    def post(self, request):
        # ── Verify the secret embedded in the URL ────────────────────────
        url_secret = request.GET.get('secret', '')
        if url_secret != settings.INTASEND_WEBHOOK_SECRET:
            logger.warning('IntaSend webhook: invalid secret — possible spoofed request')
            return HttpResponse(status=401)

        payload     = request.data
        invoice_id  = payload.get('invoice_id', '')
        state       = payload.get('state', '')
        api_ref     = payload.get('api_ref', '')   # our order_number

        logger.info(
            'IntaSend webhook: api_ref=%s invoice_id=%s state=%s',
            api_ref, invoice_id, state,
        )

        if not invoice_id or not api_ref:
            logger.error('IntaSend webhook: missing invoice_id or api_ref. payload=%s', payload)
            return HttpResponse(status=200)   # always 200 to stop retries

        if state == 'COMPLETE':
            # Find the Payment by our api_ref (order_number)
            payment = Payment.objects(api_ref=api_ref).first()
            if not payment:
                logger.error('Webhook: no Payment found for api_ref=%s', api_ref)
                return HttpResponse(status=200)

            # Re-verify with IntaSend before fulfilling — never trust webhook payload alone
            try:
                service = _get_intasend_service()
                result  = service.collect.status(invoice_id=invoice_id)
                verified_state = result.get('invoice', {}).get('state', '')
            except Exception as e:
                logger.error('Webhook IntaSend re-verify error: %s', str(e))
                return HttpResponse(status=200)

            if verified_state == 'COMPLETE':
                _fulfill_order(payment, invoice_id)
            else:
                logger.warning(
                    'Webhook state was COMPLETE but re-verify returned %s. api_ref=%s',
                    verified_state, api_ref,
                )

        elif state in ('FAILED', 'CANCELLED'):
            payment = Payment.objects(api_ref=api_ref).first()
            if payment and payment.status != 'succeeded':
                payment.status = 'failed'
                payment.save()

        # Always return 200 — IntaSend retries on non-2xx
        return HttpResponse(status=200)

# ── DEV ONLY — remove before production deployment ────────────────────────────
from django.conf import settings as django_settings

class DevMarkOrderPaidView(APIView):
    """
    POST /api/v1/payments/dev-confirm/
    Body: { "order_id": "<string>" }

    DEVELOPMENT ONLY — manually marks an order as paid and decrements stock.
    This endpoint is disabled in production (DEBUG=False).

    Remove this view and its URL before deploying.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Hard block in production — this must never be reachable live
        if not django_settings.DEBUG:
            from rest_framework.response import Response as R
            return R({'detail': 'Not found.'}, status=404)

        order_id_str = request.data.get('order_id', '').strip()
        if not order_id_str:
            return Response({'detail': 'order_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order_oid = ObjectId(order_id_str)
        except (bson_errors.InvalidId, TypeError):
            return Response({'detail': 'Invalid order_id.'}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects(id=order_oid, user_id=request.user.id).first()
        if not order:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        if order.status != 'pending':
            return Response(
                {'detail': f'Order is already {order.status}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create a Payment document to keep the data model consistent
        payment = Payment(
            order_id   = order.id,
            api_ref    = order.order_number,
            intasend_checkout_id = f'dev-{str(order.id)}',  # dummy value for dev only
            amount     = order.total,
            currency   = 'KES',
            status     = 'pending',
        )
        payment.save()

        # Fulfill exactly the same way the real webhook does
        _fulfill_order(payment, invoice_id=f'DEV-{str(order.id)}')

        return Response({
            'detail':       'Order marked as paid (dev only).',
            'order_number': order.order_number,
            'status':       'paid',
        })