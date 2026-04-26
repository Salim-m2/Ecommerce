# config/urls.py

from django.urls import path, include

urlpatterns = [
    # All API routes are versioned under /api/v1/
    path('api/v1/', include([

        # Authentication (register, login, logout, refresh, password reset)
        path('auth/', include('apps.authentication.urls')),

        # Users (profile, addresses — built in Week 10)
        path('users/', include('apps.users.urls')),

        path("", include("apps.products.urls")),

        path('', include('apps.cart.urls')),

        path('', include('apps.orders.urls')),
        path('', include('apps.payments.urls')),
    ])),
]

