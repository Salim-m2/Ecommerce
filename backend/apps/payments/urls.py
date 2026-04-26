from django.urls import path
from apps.payments.views import (
    InitializePaymentView,
    VerifyPaymentView,
    IntaSendWebhookView,
    DevMarkOrderPaidView,
)

urlpatterns = [
    path('payments/initialize/', InitializePaymentView.as_view(), name='payment-initialize'),
    path('payments/verify/',     VerifyPaymentView.as_view(),     name='payment-verify'),
    path('payments/webhook/',    IntaSendWebhookView.as_view(),   name='intasend-webhook'),
    path('payments/dev-confirm/',  DevMarkOrderPaidView.as_view(),    name='payment-dev-confirm'),
]