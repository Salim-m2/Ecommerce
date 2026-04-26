from mongoengine import (
    Document,
    StringField, ObjectIdField, FloatField,
    DateTimeField, DictField,
)
from datetime import datetime


class Payment(Document):
    """
    One Payment document per IntaSend checkout session.

    Key fields:
    - api_ref:               Our order number, sent to IntaSend as a custom
                             reference. Returned in webhooks so we can identify
                             which order a webhook belongs to.
    - intasend_checkout_id:  The UUID IntaSend assigns to the checkout session.
                             Returned in both the checkout creation response AND
                             in the redirect URL (?checkout_id=...). This is our
                             primary lookup key when the user is redirected back.
    - intasend_invoice_id:   The short tracking ID (e.g. NR5XKGY) assigned after
                             the user initiates payment. Used to verify status
                             via service.collect.status(invoice_id=...).
                             Set after the user completes payment.

    Idempotency:
    Before fulfilling an order, check payment.status == 'succeeded'.
    If already succeeded, skip — the webhook or verify endpoint fired twice.
    """
    PAYMENT_STATUSES = ['pending', 'succeeded', 'failed', 'refunded']

    order_id               = ObjectIdField(required=True)
    api_ref                = StringField(required=True)       # our order_number sent to IntaSend
    intasend_checkout_id   = StringField(unique=True)         # UUID from checkout creation
    intasend_invoice_id    = StringField()                    # short ID for status checks
    amount                 = FloatField(required=True)
    currency               = StringField(default='KES')
    status                 = StringField(default='pending', choices=PAYMENT_STATUSES)
    metadata               = DictField()
    created_at             = DateTimeField(default=datetime.utcnow)
    updated_at             = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'payments',
        'indexes': [
            {'fields': ['intasend_checkout_id'], 'unique': True, 'sparse': True},
            {'fields': ['intasend_invoice_id'],  'sparse': True},
            {'fields': ['order_id']},
            {'fields': ['api_ref']},
        ],
    }

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
