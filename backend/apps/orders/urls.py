from django.urls import path
from apps.orders.views import OrderListCreateView, OrderDetailView

urlpatterns = [
    # GET  /api/v1/orders/               → list user's orders
    # POST /api/v1/orders/               → create order from cart
    path('orders/', OrderListCreateView.as_view(), name='order-list-create'),

    # GET  /api/v1/orders/{order_number}/ → full order detail
    path('orders/<str:order_number>/', OrderDetailView.as_view(), name='order-detail'),
]