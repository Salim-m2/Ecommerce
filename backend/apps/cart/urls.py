from django.urls import path
from .views import (
    CartDetailView,
    CartItemAddView,
    CartItemDetailView,
    CartMergeView,
    CartCouponView,
)

urlpatterns = [
    # GET  /api/v1/cart/
    path('cart/', CartDetailView.as_view(), name='cart-detail'),

    # POST /api/v1/cart/items/
    path('cart/items/', CartItemAddView.as_view(), name='cart-item-add'),

    # PATCH  /api/v1/cart/items/{n}/
    # DELETE /api/v1/cart/items/{n}/
    path('cart/items/<int:item_index>/', CartItemDetailView.as_view(), name='cart-item-detail'),

    # POST /api/v1/cart/coupon/  — skeleton, real logic in Week 10
    path('cart/coupon/', CartCouponView.as_view(), name='cart-coupon'),

    # POST /api/v1/cart/merge/   — called after login
    path('cart/merge/', CartMergeView.as_view(), name='cart-merge'),
]