from django.urls import path
from apps.products.views import ProductListView, ProductDetailView, CategoryListView
from apps.products.image_views import ProductImageUploadView

urlpatterns = [
    # Category tree — put before the slug pattern so /categories/ is never
    # mistakenly matched as a product slug
    path("categories/", CategoryListView.as_view(), name="category-list"),

    # Product list and filtering
    path("products/", ProductListView.as_view(), name="product-list"),

    # Product image upload.
    path("products/upload-image/", ProductImageUploadView.as_view(), name="product-image-upload"),

    # Product detail — slug is URL-safe (lowercase letters, digits, hyphens only)
    path("products/<slug:slug>/", ProductDetailView.as_view(), name="product-detail"),
]
