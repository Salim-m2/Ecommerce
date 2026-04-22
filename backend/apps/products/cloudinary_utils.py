"""
Cloudinary helpers for product image management.

All image storage goes through this module — no other file should import
cloudinary directly. This makes it easy to swap Cloudinary for S3 later
by only changing this file.

Cloudinary is configured in settings/base.py via cloudinary.config().
The configuration is global, so we just import and call cloudinary functions.
"""
import logging
import re

import cloudinary
import cloudinary.uploader

logger = logging.getLogger(__name__)

# Maximum allowed upload size: 5 MB
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024

# Allowed MIME types — we check content_type, not the filename extension,
# because extensions can be spoofed (e.g. renaming malware.exe to malware.jpg)
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}

# Human-readable label for error messages
ALLOWED_TYPES_LABEL = "JPEG, PNG, or WebP"


def upload_product_image(file, product_slug: str) -> dict:
    """
    Upload a product image to Cloudinary.

    Args:
        file:         Django InMemoryUploadedFile or TemporaryUploadedFile
                      (the object from request.FILES['image'])
        product_slug: The product's slug string, used as the Cloudinary folder name
                      so images are organised as: ecommerce/products/{slug}/

    Returns:
        {
            "url":        str  — HTTPS Cloudinary URL
            "public_id":  str  — Cloudinary public ID (needed for deletion)
        }

    Raises:
        ValueError if the file type or size is invalid.
        Exception  if the Cloudinary upload itself fails (network, auth, etc.)
    """
    # ── Validate content type ─────────────────────────────────────────────
    content_type = getattr(file, 'content_type', '').lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(
            f"Invalid file type '{content_type}'. "
            f"Only {ALLOWED_TYPES_LABEL} images are allowed."
        )

    # ── Validate file size ────────────────────────────────────────────────
    # file.size is set by Django's file upload handling
    file_size = getattr(file, 'size', 0)
    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"File size {file_size / (1024*1024):.1f}MB exceeds the 5MB limit."
        )

    # ── Sanitise the folder path ──────────────────────────────────────────
    # product_slug is already URL-safe (only lowercase, digits, hyphens),
    # but we strip anything unexpected to be safe before using it in a path.
    safe_slug = re.sub(r'[^a-z0-9\-]', '', product_slug)
    folder = f"ecommerce/products/{safe_slug}"

    # ── Upload to Cloudinary ──────────────────────────────────────────────
    # transformation: auto-format (serves WebP to browsers that support it),
    #                 auto-quality (Cloudinary picks the best compression),
    #                 max width 1200px (no upscaling, just a cap for large uploads)
    result = cloudinary.uploader.upload(
        file,
        folder=folder,
        transformation=[
            {"fetch_format": "auto", "quality": "auto", "width": 1200, "crop": "limit"},
        ],
        resource_type="image",
    )

    logger.info(f"Uploaded image for product '{product_slug}': {result['secure_url']}")

    return {
        "url":       result["secure_url"],
        "public_id": result["public_id"],
    }


def delete_cloudinary_image(public_id: str) -> bool:
    """
    Delete an image from Cloudinary by its public ID.

    Args:
        public_id: The Cloudinary public_id string returned from upload_product_image().
                   Example: "ecommerce/products/air-jordan-1/abc123xyz"

    Returns:
        True  if deletion was successful
        False if deletion failed (logs the error, does not raise)

    Why not raise on failure?
    Deletion is called when an admin removes a product image. If Cloudinary
    is temporarily unavailable, we don't want the entire admin action to fail.
    The image becomes orphaned on Cloudinary, but the DB record is still updated.
    """
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type="image")
        success = result.get("result") == "ok"
        if success:
            logger.info(f"Deleted Cloudinary image: {public_id}")
        else:
            logger.warning(f"Cloudinary deletion returned non-ok result for '{public_id}': {result}")
        return success
    except Exception as e:
        logger.error(f"Failed to delete Cloudinary image '{public_id}': {e}")
        return False


def get_optimized_url(cloudinary_url: str, width: int = 400) -> str:
    """
    Insert Cloudinary transformation parameters into an existing URL.

    Used to generate thumbnails for product cards without re-uploading.
    Cloudinary applies transformations on-the-fly and caches the result on its CDN.

    Example:
        Input:  "https://res.cloudinary.com/mycloud/image/upload/v123/ecommerce/products/slug/img.jpg"
        Output: "https://res.cloudinary.com/mycloud/image/upload/w_400,f_auto,q_auto/v123/ecommerce/products/slug/img.jpg"

    Args:
        cloudinary_url: A full Cloudinary secure_url string
        width:          Desired width in pixels (default 400 for product cards)

    Returns:
        The URL with transformation inserted, or the original URL unchanged
        if it doesn't look like a Cloudinary upload URL (safe fallback).
    """
    transformation = f"w_{width},f_auto,q_auto"

    # Insert transformation string after "/upload/" in the URL
    if "/image/upload/" in cloudinary_url:
        return cloudinary_url.replace(
            "/image/upload/",
            f"/image/upload/{transformation}/",
            1,  # Replace only the first occurrence
        )

    # Not a Cloudinary URL (e.g. placeholder from seeding) — return as-is
    logger.debug(f"get_optimized_url: URL does not contain '/image/upload/', returning unchanged.")
    return cloudinary_url