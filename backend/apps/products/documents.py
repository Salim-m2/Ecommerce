import uuid
import re
from datetime import datetime
from mongoengine import (
    Document,
    EmbeddedDocument,
    StringField,
    FloatField,
    IntField,
    BooleanField,
    DateTimeField,
    ListField,
    EmbeddedDocumentField,
    ObjectIdField,
)


class Variant(EmbeddedDocument):
    """
    Embedded inside Product — not a separate collection.
    Each variant represents a specific size/color combination of a product.
    Embedding is correct here because variants are always read with their product
    and the list is bounded (no product has 10,000 variants).
    """
    variant_id = StringField(required=True)       # UUID string, set on creation
    size       = StringField()                    # e.g. "42", "L", "XL" — optional
    color      = StringField()                    # e.g. "Black/Red" — optional
    sku        = StringField(required=True)        # Stock Keeping Unit — unique within product
    price      = FloatField(required=True, min_value=0)  # Can differ from base_price
    stock      = IntField(default=0, min_value=0)
    images     = ListField(StringField())          # Cloudinary URLs specific to this variant

    def __str__(self):
        return f"Variant({self.sku}, size={self.size}, color={self.color})"


class Product(Document):
    """
    Main product document. Variants are embedded (not referenced) because:
    - Variants are always fetched with the product, never independently
    - The list is small and bounded
    - Embedding avoids extra queries
    """
    seller_id    = ObjectIdField(required=True)     # Ref to User._id
    category_id  = ObjectIdField(required=True)     # Ref to Category._id
    name         = StringField(required=True, max_length=200)
    slug         = StringField(required=True, unique=True)  # URL-safe, e.g. "air-jordan-1-retro"
    description  = StringField(required=True)
    brand        = StringField()
    base_price   = FloatField(required=True, min_value=0)   # Lowest/default price shown on listing
    images       = ListField(StringField())          # Cloudinary URLs, product-level
    tags         = ListField(StringField())          # e.g. ["sneakers", "basketball"]
    variants     = ListField(EmbeddedDocumentField(Variant))
    avg_rating   = FloatField(default=0.0)
    review_count = IntField(default=0)
    is_active    = BooleanField(default=True)
    created_at   = DateTimeField(default=datetime.utcnow)
    updated_at   = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'products',
        'ordering': ['-created_at'],
    }

    def save(self, *args, **kwargs):
        # Always stamp updated_at on every save — lets us sort by "recently updated"
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

    @classmethod
    def generate_slug(cls, name):
        """
        Convert a product name to a URL-safe slug.
        'Air Jordan 1 Retro!' -> 'air-jordan-1-retro'
        """
        slug = name.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)     # Remove special characters
        slug = re.sub(r'[\s_]+', '-', slug)       # Spaces and underscores -> hyphens
        slug = re.sub(r'-+', '-', slug)           # Collapse multiple hyphens
        slug = slug.strip('-')
        return slug

    @classmethod
    def generate_unique_slug(cls, name):
        """
        Appends a short UUID suffix if the base slug is already taken.
        Call this during product creation, not generate_slug() directly.
        """
        base_slug = cls.generate_slug(name)
        slug = base_slug
        counter = 1
        while cls.objects(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def __str__(self):
        return f"Product({self.name}, slug={self.slug})"


class Category(Document):
    """
    Flat collection — tree structure is built in Python by matching parent_id.
    Why flat? MongoDB doesn't have a native tree type, and our category tree
    is small enough to fetch all at once and build in memory.
    """
    name      = StringField(required=True, unique=True)
    slug      = StringField(required=True, unique=True)
    parent_id = ObjectIdField(null=True, default=None)  # null = top-level category
    image_url = StringField()                            # Cloudinary URL
    order     = IntField(default=0)                      # Controls display ordering

    meta = {
        'collection': 'categories',
        'ordering': ['order', 'name'],
    }

    def __str__(self):
        return f"Category({self.name})"