"""
Image upload endpoint for product images.

Separated from views.py intentionally — image upload has different
concerns (multipart parsing, file validation, Cloudinary) from the
read-only product listing/detail views.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

from apps.core.permissions import IsAdminOrSeller
from apps.products.cloudinary_utils import upload_product_image


class ProductImageUploadView(APIView):
    """
    POST /api/v1/products/upload-image/

    Accepts multipart form data with:
        image        (required) — the image file
        product_slug (required) — the product slug used as the Cloudinary folder name

    Returns:
        200 { "url": "https://...", "public_id": "ecommerce/products/slug/abc123" }
        400 if file is missing, wrong type, or too large
        401 if not authenticated
        403 if authenticated but not admin or seller

    Why require product_slug in the request body?
    Images are organised in Cloudinary under ecommerce/products/{slug}/.
    The slug must be provided at upload time so the folder is set correctly.
    The frontend sends the slug from the product form before the product is saved,
    which is fine — Cloudinary folders are created implicitly on first upload.
    """
    permission_classes = [IsAdminOrSeller]

    # MultiPartParser handles file uploads (multipart/form-data)
    # FormParser handles the accompanying text fields (product_slug)
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        # ── Validate image file presence ──────────────────────────────────
        image_file = request.FILES.get("image")
        if not image_file:
            return Response(
                {"detail": "No image file provided. Send the file under the key 'image'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Validate product_slug presence ────────────────────────────────
        product_slug = request.data.get("product_slug", "").strip()
        if not product_slug:
            return Response(
                {"detail": "product_slug is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Upload via utility (handles type/size validation + Cloudinary) ─
        try:
            result = upload_product_image(image_file, product_slug)
        except ValueError as e:
            # File type or size validation failed — client error
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            # Cloudinary API error — server error, log it
            return Response(
                {"detail": "Image upload failed. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(result, status=status.HTTP_200_OK)