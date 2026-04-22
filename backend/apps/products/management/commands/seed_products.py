"""
Management command: python manage.py seed_products

Seeds the database with realistic test data:
  - 5 top-level categories
  - 3 subcategories under Footwear
  - 50 products spread across categories, each with 2-4 variants

Usage:
  python manage.py seed_products               # Use placeholder Cloudinary demo URL
  python manage.py seed_products --clear       # Drop existing data first
"""
import uuid
import random
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from bson import ObjectId

from apps.products.documents import Product, Category, Variant
from apps.users.documents import User


# ─────────────────────────────────────────────
# Seed data definitions
# ─────────────────────────────────────────────

PLACEHOLDER_IMAGE = "https://res.cloudinary.com/demo/image/upload/sample.jpg"

CATEGORIES = [
    # (name, slug, parent_slug or None, order)
    ("Electronics",      "electronics",       None,          1),
    ("Footwear",         "footwear",          None,          2),
    ("Clothing",         "clothing",          None,          3),
    ("Home and Kitchen", "home-and-kitchen",  None,          4),
    ("Sports",           "sports",            None,          5),
    # Subcategories of Footwear
    ("Sneakers",         "sneakers",          "footwear",    1),
    ("Sandals",          "sandals",           "footwear",    2),
    ("Boots",            "boots",             "footwear",    3),
]

PRODUCTS_DATA = [
    # Electronics
    {
        "name": "Sony WH-1000XM5 Headphones",
        "brand": "Sony",
        "category": "electronics",
        "base_price": 279.99,
        "description": "Industry-leading noise cancelling wireless headphones with 30-hour battery life and multipoint connection for seamless switching between two devices.",
        "tags": ["headphones", "wireless", "noise-cancelling", "sony", "audio"],
        "variants": [
            {"color": "Black", "size": None, "sku": "WH1000XM5-BLK", "price": 279.99, "stock": 25},
            {"color": "Silver", "size": None, "sku": "WH1000XM5-SLV", "price": 279.99, "stock": 18},
        ],
    },
    {
        "name": "Apple AirPods Pro 2nd Gen",
        "brand": "Apple",
        "category": "electronics",
        "base_price": 249.00,
        "description": "Active noise cancellation, transparency mode, and adaptive audio. H2 chip delivers smarter, more powerful noise cancellation.",
        "tags": ["earbuds", "wireless", "apple", "noise-cancelling", "audio"],
        "variants": [
            {"color": "White", "size": None, "sku": "AIRPODSPRO2-WHT", "price": 249.00, "stock": 40},
        ],
    },
    {
        "name": "Samsung 27-inch 4K Monitor",
        "brand": "Samsung",
        "category": "electronics",
        "base_price": 349.99,
        "description": "Ultra HD 4K resolution, 60Hz refresh rate, HDR10 support. IPS panel with 178° viewing angles.",
        "tags": ["monitor", "4k", "samsung", "display", "uhd"],
        "variants": [
            {"color": "Black", "size": "27 inch", "sku": "SAM-MON-27-4K", "price": 349.99, "stock": 12},
            {"color": "Black", "size": "32 inch", "sku": "SAM-MON-32-4K", "price": 449.99, "stock": 8},
        ],
    },
    {
        "name": "Logitech MX Master 3S Mouse",
        "brand": "Logitech",
        "category": "electronics",
        "base_price": 99.99,
        "description": "Advanced wireless mouse for power users. 8K DPI sensor, MagSpeed scroll wheel, and ergonomic design for all-day comfort.",
        "tags": ["mouse", "wireless", "logitech", "productivity", "ergonomic"],
        "variants": [
            {"color": "Graphite", "size": None, "sku": "MXM3S-GRY", "price": 99.99, "stock": 30},
            {"color": "Pale Grey", "size": None, "sku": "MXM3S-PLG", "price": 99.99, "stock": 22},
        ],
    },
    {
        "name": "Mechanical Keyboard TKL",
        "brand": "Keychron",
        "category": "electronics",
        "base_price": 89.99,
        "description": "Tenkeyless mechanical keyboard with hot-swappable switches, RGB backlighting, and Bluetooth 5.1 for multi-device use.",
        "tags": ["keyboard", "mechanical", "rgb", "keychron", "tenkeyless"],
        "variants": [
            {"color": "Space Grey", "size": "Red Switches", "sku": "KC-TKL-RED", "price": 89.99, "stock": 15},
            {"color": "Space Grey", "size": "Brown Switches", "sku": "KC-TKL-BRN", "price": 89.99, "stock": 20},
            {"color": "Space Grey", "size": "Blue Switches", "sku": "KC-TKL-BLU", "price": 89.99, "stock": 10},
        ],
    },
    {
        "name": "Anker 65W USB-C Charger",
        "brand": "Anker",
        "category": "electronics",
        "base_price": 45.99,
        "description": "Compact 65W USB-C charger with GaN technology. Charges laptop, tablet, and phone simultaneously.",
        "tags": ["charger", "usb-c", "gan", "anker", "fast-charging"],
        "variants": [
            {"color": "Black", "size": "1-Port 65W", "sku": "ANK-65W-1P", "price": 35.99, "stock": 50},
            {"color": "Black", "size": "3-Port 65W", "sku": "ANK-65W-3P", "price": 45.99, "stock": 35},
        ],
    },

    # Footwear - Sneakers
    {
        "name": "Air Jordan 1 Retro High OG",
        "brand": "Nike",
        "category": "sneakers",
        "base_price": 120.00,
        "description": "The Air Jordan 1 Retro High OG brings back a classic silhouette with premium leather construction and visible Air cushioning.",
        "tags": ["sneakers", "basketball", "nike", "jordan", "retro"],
        "variants": [
            {"color": "Black/Red", "size": "40", "sku": "AJ1-40-BR", "price": 120.00, "stock": 8},
            {"color": "Black/Red", "size": "41", "sku": "AJ1-41-BR", "price": 120.00, "stock": 12},
            {"color": "Black/Red", "size": "42", "sku": "AJ1-42-BR", "price": 120.00, "stock": 15},
            {"color": "Black/Red", "size": "43", "sku": "AJ1-43-BR", "price": 120.00, "stock": 10},
            {"color": "White/Blue", "size": "42", "sku": "AJ1-42-WB", "price": 120.00, "stock": 5},
        ],
    },
    {
        "name": "Adidas Ultraboost 23",
        "brand": "Adidas",
        "category": "sneakers",
        "base_price": 190.00,
        "description": "Premium running shoe with BOOST midsole technology for incredible energy return. Primeknit upper adapts to the shape of your foot.",
        "tags": ["running", "adidas", "boost", "sneakers", "performance"],
        "variants": [
            {"color": "Core Black", "size": "40", "sku": "UB23-40-BLK", "price": 190.00, "stock": 10},
            {"color": "Core Black", "size": "42", "sku": "UB23-42-BLK", "price": 190.00, "stock": 14},
            {"color": "Cloud White", "size": "41", "sku": "UB23-41-WHT", "price": 190.00, "stock": 9},
            {"color": "Cloud White", "size": "43", "sku": "UB23-43-WHT", "price": 190.00, "stock": 6},
        ],
    },
    {
        "name": "New Balance 574 Classic",
        "brand": "New Balance",
        "category": "sneakers",
        "base_price": 89.99,
        "description": "A timeless silhouette updated with ENCAP midsole technology. The 574 is versatile enough for everyday wear.",
        "tags": ["sneakers", "lifestyle", "new-balance", "classic", "casual"],
        "variants": [
            {"color": "Grey/White", "size": "40", "sku": "NB574-40-GW", "price": 89.99, "stock": 20},
            {"color": "Grey/White", "size": "42", "sku": "NB574-42-GW", "price": 89.99, "stock": 18},
            {"color": "Navy/Red", "size": "41", "sku": "NB574-41-NR", "price": 89.99, "stock": 12},
        ],
    },
    {
        "name": "Vans Old Skool Classic",
        "brand": "Vans",
        "category": "sneakers",
        "base_price": 65.00,
        "description": "The iconic low-top with the famous side stripe. Suede and canvas upper with cushioned footbed for all-day comfort.",
        "tags": ["skateboarding", "vans", "lifestyle", "sneakers", "canvas"],
        "variants": [
            {"color": "Black/White", "size": "39", "sku": "VOS-39-BW", "price": 65.00, "stock": 25},
            {"color": "Black/White", "size": "41", "sku": "VOS-41-BW", "price": 65.00, "stock": 30},
            {"color": "Navy/White", "size": "40", "sku": "VOS-40-NW", "price": 65.00, "stock": 22},
        ],
    },

    # Footwear - Sandals
    {
        "name": "Birkenstock Arizona Sandal",
        "brand": "Birkenstock",
        "category": "sandals",
        "base_price": 99.99,
        "description": "The iconic two-strap sandal with contoured cork footbed that molds to the shape of your foot for custom fit.",
        "tags": ["sandals", "birkenstock", "cork", "casual", "comfort"],
        "variants": [
            {"color": "Birko-Flor Black", "size": "38", "sku": "BIRK-ARZ-38-BLK", "price": 99.99, "stock": 15},
            {"color": "Birko-Flor Black", "size": "40", "sku": "BIRK-ARZ-40-BLK", "price": 99.99, "stock": 20},
            {"color": "Natural Suede", "size": "39", "sku": "BIRK-ARZ-39-NAT", "price": 119.99, "stock": 10},
        ],
    },
    {
        "name": "Teva Original Universal Sandal",
        "brand": "Teva",
        "category": "sandals",
        "base_price": 50.00,
        "description": "The original sport sandal with four-point adjustable straps and EVA foam midsole for cushioning on any terrain.",
        "tags": ["sandals", "teva", "outdoor", "sport", "water"],
        "variants": [
            {"color": "Desert Sage", "size": "40", "sku": "TEVA-ORIG-40-DS", "price": 50.00, "stock": 18},
            {"color": "Black", "size": "42", "sku": "TEVA-ORIG-42-BLK", "price": 50.00, "stock": 22},
        ],
    },

    # Footwear - Boots
    {
        "name": "Timberland 6-Inch Premium Boot",
        "brand": "Timberland",
        "category": "boots",
        "base_price": 198.00,
        "description": "Waterproof nubuck leather boots with padded collar and lug outsole. A true icon since 1973.",
        "tags": ["boots", "waterproof", "timberland", "leather", "work"],
        "variants": [
            {"color": "Wheat Nubuck", "size": "41", "sku": "TIMB-6IN-41-WHT", "price": 198.00, "stock": 12},
            {"color": "Wheat Nubuck", "size": "43", "sku": "TIMB-6IN-43-WHT", "price": 198.00, "stock": 9},
            {"color": "Black", "size": "42", "sku": "TIMB-6IN-42-BLK", "price": 198.00, "stock": 7},
        ],
    },

    # Clothing
    {
        "name": "Champion Reverse Weave Hoodie",
        "brand": "Champion",
        "category": "clothing",
        "base_price": 65.00,
        "description": "The original reverse weave construction reduces shrinkage. Heavyweight cotton fleece for lasting warmth.",
        "tags": ["hoodie", "champion", "fleece", "casual", "sweatshirt"],
        "variants": [
            {"color": "Oxford Grey", "size": "S", "sku": "CHAMP-RW-S-OG", "price": 65.00, "stock": 20},
            {"color": "Oxford Grey", "size": "M", "sku": "CHAMP-RW-M-OG", "price": 65.00, "stock": 35},
            {"color": "Oxford Grey", "size": "L", "sku": "CHAMP-RW-L-OG", "price": 65.00, "stock": 28},
            {"color": "Oxford Grey", "size": "XL", "sku": "CHAMP-RW-XL-OG", "price": 65.00, "stock": 15},
            {"color": "Navy", "size": "M", "sku": "CHAMP-RW-M-NAV", "price": 65.00, "stock": 22},
        ],
    },
    {
        "name": "Levi's 501 Original Jeans",
        "brand": "Levi's",
        "category": "clothing",
        "base_price": 79.99,
        "description": "The original jeans. Straight fit, button fly, and iconic 501 styling since 1873. Made with 100% cotton denim.",
        "tags": ["jeans", "denim", "levis", "classic", "straight-fit"],
        "variants": [
            {"color": "Dark Stonewash", "size": "30x32", "sku": "LEV-501-30-32-DS", "price": 79.99, "stock": 15},
            {"color": "Dark Stonewash", "size": "32x32", "sku": "LEV-501-32-32-DS", "price": 79.99, "stock": 20},
            {"color": "Light Wash", "size": "32x34", "sku": "LEV-501-32-34-LW", "price": 79.99, "stock": 12},
            {"color": "Light Wash", "size": "34x32", "sku": "LEV-501-34-32-LW", "price": 79.99, "stock": 8},
        ],
    },
    {
        "name": "Uniqlo Heattech Crewneck",
        "brand": "Uniqlo",
        "category": "clothing",
        "base_price": 19.99,
        "description": "Heattech technology generates heat from your body moisture to keep you warm. Ultra lightweight and stretchy.",
        "tags": ["thermal", "uniqlo", "heattech", "winter", "base-layer"],
        "variants": [
            {"color": "Black", "size": "S", "sku": "UNI-HT-S-BLK", "price": 19.99, "stock": 40},
            {"color": "Black", "size": "M", "sku": "UNI-HT-M-BLK", "price": 19.99, "stock": 50},
            {"color": "Black", "size": "L", "sku": "UNI-HT-L-BLK", "price": 19.99, "stock": 45},
            {"color": "White", "size": "M", "sku": "UNI-HT-M-WHT", "price": 19.99, "stock": 38},
        ],
    },
    {
        "name": "Patagonia Better Sweater Fleece",
        "brand": "Patagonia",
        "category": "clothing",
        "base_price": 139.00,
        "description": "Classic zip-through fleece made from 100% recycled polyester. Full-zip sweater-knit jacket for versatile layering.",
        "tags": ["fleece", "patagonia", "outdoor", "recycled", "jacket"],
        "variants": [
            {"color": "Black", "size": "S", "sku": "PAT-BS-S-BLK", "price": 139.00, "stock": 8},
            {"color": "Black", "size": "M", "sku": "PAT-BS-M-BLK", "price": 139.00, "stock": 12},
            {"color": "Oatmeal", "size": "L", "sku": "PAT-BS-L-OAT", "price": 139.00, "stock": 6},
        ],
    },
    {
        "name": "Nike Dri-FIT Running Shorts",
        "brand": "Nike",
        "category": "clothing",
        "base_price": 35.00,
        "description": "Sweat-wicking Dri-FIT fabric keeps you dry during intense runs. 7-inch inseam with built-in liner and zip pocket.",
        "tags": ["shorts", "running", "nike", "dri-fit", "sport"],
        "variants": [
            {"color": "Black", "size": "S", "sku": "NK-DRFT-S-BLK", "price": 35.00, "stock": 30},
            {"color": "Black", "size": "M", "sku": "NK-DRFT-M-BLK", "price": 35.00, "stock": 40},
            {"color": "Navy", "size": "L", "sku": "NK-DRFT-L-NAV", "price": 35.00, "stock": 25},
        ],
    },
    {
        "name": "Carhartt WIP Chase Sweatshirt",
        "brand": "Carhartt WIP",
        "category": "clothing",
        "base_price": 79.00,
        "description": "Heavyweight sweatshirt with brushed back fleece for warmth. Relaxed fit with embroidered chest logo.",
        "tags": ["sweatshirt", "carhartt", "workwear", "casual", "fleece"],
        "variants": [
            {"color": "Dark Navy", "size": "S", "sku": "CARR-CH-S-DN", "price": 79.00, "stock": 14},
            {"color": "Dark Navy", "size": "M", "sku": "CARR-CH-M-DN", "price": 79.00, "stock": 22},
            {"color": "Dark Navy", "size": "L", "sku": "CARR-CH-L-DN", "price": 79.00, "stock": 18},
            {"color": "Black", "size": "XL", "sku": "CARR-CH-XL-BLK", "price": 79.00, "stock": 10},
        ],
    },
    {
        "name": "Arc'teryx Atom LT Vest",
        "brand": "Arc'teryx",
        "category": "clothing",
        "base_price": 249.00,
        "description": "Lightweight insulated vest with Coreloft synthetic insulation. Packable, wind-resistant shell for alpine use.",
        "tags": ["vest", "arcteryx", "insulated", "outdoor", "technical"],
        "variants": [
            {"color": "Black", "size": "S", "sku": "ARC-ALT-S-BLK", "price": 249.00, "stock": 5},
            {"color": "Black", "size": "M", "sku": "ARC-ALT-M-BLK", "price": 249.00, "stock": 8},
            {"color": "Pilot", "size": "L", "sku": "ARC-ALT-L-PLT", "price": 249.00, "stock": 4},
        ],
    },
    {
        "name": "Columbia PFG Omni-Shade Shirt",
        "brand": "Columbia",
        "category": "clothing",
        "base_price": 50.00,
        "description": "Built-in UPF 40 sun protection. Omni-Wick sweat management keeps you cool on the water or trail.",
        "tags": ["shirt", "columbia", "upf", "fishing", "outdoor"],
        "variants": [
            {"color": "Vivid Blue", "size": "M", "sku": "COL-PFG-M-VB", "price": 50.00, "stock": 25},
            {"color": "Vivid Blue", "size": "L", "sku": "COL-PFG-L-VB", "price": 50.00, "stock": 20},
            {"color": "White", "size": "XL", "sku": "COL-PFG-XL-WHT", "price": 50.00, "stock": 15},
        ],
    },
    {
        "name": "The North Face Base Camp Hat",
        "brand": "The North Face",
        "category": "clothing",
        "base_price": 30.00,
        "description": "Classic five-panel camp hat with embroidered logo. One-size-fits-most adjustable back strap.",
        "tags": ["hat", "cap", "north-face", "outdoor", "casual"],
        "variants": [
            {"color": "Summit Navy", "size": "One Size", "sku": "TNF-BCH-OS-SN", "price": 30.00, "stock": 50},
            {"color": "Black", "size": "One Size", "sku": "TNF-BCH-OS-BLK", "price": 30.00, "stock": 45},
        ],
    },
    {
        "name": "Essentials Oversized Tee",
        "brand": "Fear of God Essentials",
        "category": "clothing",
        "base_price": 45.00,
        "description": "Boxy oversized silhouette in heavyweight jersey cotton. Dropped shoulders, crew neck, rubberized logo.",
        "tags": ["t-shirt", "essentials", "streetwear", "oversized", "cotton"],
        "variants": [
            {"color": "Taupe", "size": "XS/S", "sku": "FOG-OT-XS-TP", "price": 45.00, "stock": 20},
            {"color": "Taupe", "size": "M/L", "sku": "FOG-OT-ML-TP", "price": 45.00, "stock": 28},
            {"color": "Black", "size": "M/L", "sku": "FOG-OT-ML-BLK", "price": 45.00, "stock": 22},
        ],
    },

    # Home and Kitchen
    {
        "name": "Instant Pot Duo 7-in-1",
        "brand": "Instant Pot",
        "category": "home-and-kitchen",
        "base_price": 79.99,
        "description": "7-in-1 multi-use pressure cooker: pressure cook, slow cook, rice cooker, steamer, sauté pan, yogurt maker, and warmer.",
        "tags": ["pressure-cooker", "instant-pot", "kitchen", "multi-cooker", "appliance"],
        "variants": [
            {"color": "Stainless", "size": "6 Quart", "sku": "IP-DUO-6QT", "price": 79.99, "stock": 30},
            {"color": "Stainless", "size": "8 Quart", "sku": "IP-DUO-8QT", "price": 99.99, "stock": 18},
        ],
    },
    {
        "name": "Vitamix 5200 Blender",
        "brand": "Vitamix",
        "category": "home-and-kitchen",
        "base_price": 349.99,
        "description": "Professional-grade blender with aircraft-grade stainless steel blades. Variable speed control for everything from smoothies to hot soups.",
        "tags": ["blender", "vitamix", "kitchen", "smoothie", "professional"],
        "variants": [
            {"color": "Black", "size": None, "sku": "VITX-5200-BLK", "price": 349.99, "stock": 10},
            {"color": "Red", "size": None, "sku": "VITX-5200-RED", "price": 349.99, "stock": 7},
        ],
    },
    {
        "name": "Le Creuset Signature Skillet",
        "brand": "Le Creuset",
        "category": "home-and-kitchen",
        "base_price": 199.99,
        "description": "Enameled cast iron skillet with long cast iron handle. Even heat distribution and retention for perfect sears.",
        "tags": ["cast-iron", "le-creuset", "skillet", "cookware", "oven-safe"],
        "variants": [
            {"color": "Cerise Red", "size": "25cm", "sku": "LC-SK-25-CR", "price": 199.99, "stock": 8},
            {"color": "Cerise Red", "size": "30cm", "sku": "LC-SK-30-CR", "price": 249.99, "stock": 6},
            {"color": "Marseille Blue", "size": "25cm", "sku": "LC-SK-25-MB", "price": 199.99, "stock": 5},
        ],
    },
    {
        "name": "Dyson V12 Detect Slim Vacuum",
        "brand": "Dyson",
        "category": "home-and-kitchen",
        "base_price": 599.99,
        "description": "Laser technology detects invisible dust on hard floors. Digital motor generates 150AW suction in boost mode.",
        "tags": ["vacuum", "dyson", "cordless", "home", "cleaning"],
        "variants": [
            {"color": "Bright Copper/Nickel", "size": None, "sku": "DYSV12-STD", "price": 599.99, "stock": 12},
        ],
    },
    {
        "name": "Fellow Stagg EKG Kettle",
        "brand": "Fellow",
        "category": "home-and-kitchen",
        "base_price": 165.00,
        "description": "Pour-over kettle with precision temperature control, stopwatch timer, and 1-liter capacity for the perfect brew.",
        "tags": ["kettle", "coffee", "fellow", "pour-over", "temperature-control"],
        "variants": [
            {"color": "Matte Black", "size": None, "sku": "FEL-EKG-BLK", "price": 165.00, "stock": 15},
            {"color": "Polished Steel", "size": None, "sku": "FEL-EKG-STL", "price": 165.00, "stock": 10},
        ],
    },
    {
        "name": "YETI Rambler 30oz Tumbler",
        "brand": "YETI",
        "category": "home-and-kitchen",
        "base_price": 38.00,
        "description": "Double-wall vacuum insulated stainless steel tumbler. Keeps drinks cold 24 hours or hot 6 hours. Dishwasher safe.",
        "tags": ["tumbler", "yeti", "insulated", "drinkware", "stainless"],
        "variants": [
            {"color": "Black", "size": "30oz", "sku": "YETI-R30-BLK", "price": 38.00, "stock": 40},
            {"color": "Charcoal", "size": "30oz", "sku": "YETI-R30-CHA", "price": 38.00, "stock": 35},
            {"color": "Navy", "size": "20oz", "sku": "YETI-R20-NAV", "price": 30.00, "stock": 28},
        ],
    },
    {
        "name": "Casper Original Pillow",
        "brand": "Casper",
        "category": "home-and-kitchen",
        "base_price": 65.00,
        "description": "Pillow-within-a-pillow design with a firm inner pillow for support and a soft outer pillow for comfort.",
        "tags": ["pillow", "casper", "sleep", "bedding", "cooling"],
        "variants": [
            {"color": "White", "size": "Standard", "sku": "CASP-PIL-STD", "price": 65.00, "stock": 30},
            {"color": "White", "size": "King", "sku": "CASP-PIL-KNG", "price": 85.00, "stock": 20},
        ],
    },
    {
        "name": "Oura Ring Gen 3",
        "brand": "Oura",
        "category": "home-and-kitchen",
        "base_price": 299.00,
        "description": "Smart ring tracking heart rate, sleep, readiness, and activity. 7-day battery, water resistant to 100m.",
        "tags": ["smart-ring", "oura", "health", "sleep-tracking", "wearable"],
        "variants": [
            {"color": "Silver", "size": "6", "sku": "OURA-G3-6-SLV", "price": 299.00, "stock": 10},
            {"color": "Silver", "size": "8", "sku": "OURA-G3-8-SLV", "price": 299.00, "stock": 12},
            {"color": "Black", "size": "9", "sku": "OURA-G3-9-BLK", "price": 299.00, "stock": 8},
        ],
    },

    # Sports
    {
        "name": "Garmin Forerunner 265 GPS Watch",
        "brand": "Garmin",
        "category": "sports",
        "base_price": 349.99,
        "description": "AMOLED display running GPS smartwatch with training readiness, Daily Suggested Workouts, and advanced health monitoring.",
        "tags": ["gps-watch", "garmin", "running", "training", "smartwatch"],
        "variants": [
            {"color": "Black/Powder Grey", "size": None, "sku": "GAR-FR265-BPG", "price": 349.99, "stock": 15},
            {"color": "Aqua/White", "size": None, "sku": "GAR-FR265-AW", "price": 349.99, "stock": 10},
        ],
    },
    {
        "name": "Hydro Flask 32oz Water Bottle",
        "brand": "Hydro Flask",
        "category": "sports",
        "base_price": 44.95,
        "description": "TempShield double-wall vacuum insulation keeps drinks cold up to 24 hours and hot up to 12. Durable 18/8 pro-grade stainless steel.",
        "tags": ["water-bottle", "hydro-flask", "insulated", "sport", "outdoor"],
        "variants": [
            {"color": "Black", "size": "32oz Wide Mouth", "sku": "HF-32WM-BLK", "price": 44.95, "stock": 50},
            {"color": "Pacific", "size": "32oz Wide Mouth", "sku": "HF-32WM-PAC", "price": 44.95, "stock": 35},
            {"color": "Black", "size": "40oz Wide Mouth", "sku": "HF-40WM-BLK", "price": 49.95, "stock": 30},
        ],
    },
    {
        "name": "TRX HOME2 Suspension Trainer",
        "brand": "TRX",
        "category": "sports",
        "base_price": 199.95,
        "description": "Full body workout using only bodyweight and gravity. Includes door anchor, two rubber handles with foot cradles.",
        "tags": ["suspension-training", "trx", "home-gym", "bodyweight", "fitness"],
        "variants": [
            {"color": "Black/Grey", "size": None, "sku": "TRX-HOME2-BG", "price": 199.95, "stock": 20},
        ],
    },
    {
        "name": "Theragun Prime Massage Gun",
        "brand": "Theragun",
        "category": "sports",
        "base_price": 299.00,
        "description": "Percussive therapy device with 4 attachments, 5 speed settings, and QuietForce Technology for near-silent operation.",
        "tags": ["massage-gun", "theragun", "recovery", "percussion", "sport"],
        "variants": [
            {"color": "Black", "size": None, "sku": "TG-PRIME-BLK", "price": 299.00, "stock": 15},
            {"color": "Sand", "size": None, "sku": "TG-PRIME-SND", "price": 299.00, "stock": 10},
        ],
    },
    {
        "name": "Manduka PRO Yoga Mat",
        "brand": "Manduka",
        "category": "sports",
        "base_price": 120.00,
        "description": "6mm dense cushioning for superior support. Non-slip surface and closed-cell technology for easy cleanup. Lifetime guarantee.",
        "tags": ["yoga", "manduka", "mat", "fitness", "non-slip"],
        "variants": [
            {"color": "Black", "size": "71 inch", "sku": "MAND-PRO-71-BLK", "price": 120.00, "stock": 18},
            {"color": "Amethyst", "size": "71 inch", "sku": "MAND-PRO-71-AME", "price": 120.00, "stock": 12},
            {"color": "Black", "size": "85 inch (Tall)", "sku": "MAND-PRO-85-BLK", "price": 140.00, "stock": 8},
        ],
    },
    {
        "name": "Wilson Clash 100 Tennis Racket",
        "brand": "Wilson",
        "category": "sports",
        "base_price": 229.00,
        "description": "FreeFlex technology for unmatched flexibility and StableSmart frame geometry for stability on every shot.",
        "tags": ["tennis", "wilson", "racket", "sport", "clash"],
        "variants": [
            {"color": "Green/Black", "size": "4 1/4 Grip", "sku": "WIL-CL100-41", "price": 229.00, "stock": 10},
            {"color": "Green/Black", "size": "4 3/8 Grip", "sku": "WIL-CL100-43", "price": 229.00, "stock": 8},
        ],
    },
    {
        "name": "Bowflex SelectTech 552 Dumbbells",
        "brand": "Bowflex",
        "category": "sports",
        "base_price": 349.00,
        "description": "Replaces 15 sets of weights. Select from 5 to 52.5 lbs with a simple turn of a dial. Anti-friction dial ensures smooth adjustments.",
        "tags": ["dumbbells", "bowflex", "adjustable", "home-gym", "strength"],
        "variants": [
            {"color": "Grey/Black", "size": "Pair (2 x 52.5lb)", "sku": "BFX-552-PAIR", "price": 349.00, "stock": 8},
            {"color": "Grey/Black", "size": "Single (52.5lb)", "sku": "BFX-552-SNGL", "price": 189.00, "stock": 12},
        ],
    },
    {
        "name": "Osprey Talon 22 Daypack",
        "brand": "Osprey",
        "category": "sports",
        "base_price": 140.00,
        "description": "Trail-tuned 22L daypack with AirSpeed suspended mesh back panel for maximum ventilation on hikes.",
        "tags": ["backpack", "osprey", "hiking", "daypack", "outdoor"],
        "variants": [
            {"color": "Volcanic Grey", "size": "XS/S", "sku": "OSP-TAL22-XS-VG", "price": 140.00, "stock": 10},
            {"color": "Volcanic Grey", "size": "M/L", "sku": "OSP-TAL22-ML-VG", "price": 140.00, "stock": 12},
            {"color": "Unity Green", "size": "M/L", "sku": "OSP-TAL22-ML-UG", "price": 140.00, "stock": 8},
        ],
    },
    {
        "name": "Adidas Predator Accuracy Football",
        "brand": "Adidas",
        "category": "sports",
        "base_price": 29.99,
        "description": "Thermally bonded seamless construction for predictable flight. FIFA Basic approved for training and recreational play.",
        "tags": ["football", "soccer", "adidas", "ball", "training"],
        "variants": [
            {"color": "White/Black/Solar Red", "size": "4", "sku": "ADI-PRED-SZ4", "price": 24.99, "stock": 30},
            {"color": "White/Black/Solar Red", "size": "5", "sku": "ADI-PRED-SZ5", "price": 29.99, "stock": 45},
        ],
    },
]


class Command(BaseCommand):
    help = "Seed the database with categories and test products"

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing products and categories before seeding',
        )
        parser.add_argument(
            '--use-cloudinary',
            action='store_true',
            help='Upload real images to Cloudinary instead of using the placeholder URL. '
                 'Requires CLOUDINARY_* env vars to be set.',
        )

    def handle(self, *args, **options):
        use_cloudinary = options['use_cloudinary']

        if options['clear']:
            self.stdout.write("🗑  Clearing existing products and categories...")
            Product.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("   Cleared."))

        # ── Step 1: Create or retrieve a seed admin user ──────────────────
        seed_seller = User.objects(email="seed@example.com").first()
        if not seed_seller:
            seed_seller = User(
                email="seed@example.com",
                first_name="Seed",
                last_name="Admin",
                role="admin",
            )
            seed_seller.set_password("SeedPassword123!")
            seed_seller.save()
            self.stdout.write("👤  Created seed admin user: seed@example.com")
        seller_id = seed_seller.id

        # ── Step 2: Create categories ──────────────────────────────────────
        self.stdout.write("📂  Creating categories...")
        category_map = {}

        for name, slug, parent_slug, order in CATEGORIES:
            existing = Category.objects(slug=slug).first()
            if existing:
                category_map[slug] = existing
                continue

            parent_id = None
            if parent_slug and parent_slug in category_map:
                parent_id = category_map[parent_slug].id

            cat = Category(
                name=name,
                slug=slug,
                parent_id=parent_id,
                image_url=PLACEHOLDER_IMAGE,
                order=order,
            )
            cat.save()
            category_map[slug] = cat
            self.stdout.write(f"   ✅ {name}")

        # ── Step 3: Optionally upload a real placeholder to Cloudinary ─────
        # When --use-cloudinary is set, we upload a single placeholder image
        # once and reuse its URL for every product. This avoids 38 separate
        # Cloudinary API calls during seeding while still testing real URLs.
        cloudinary_seed_url = None
        if use_cloudinary:
            self.stdout.write("☁️   Uploading placeholder image to Cloudinary...")
            try:
                import urllib.request
                import tempfile
                import os
                from apps.products.cloudinary_utils import upload_product_image

                # Download the demo image to a temp file
                demo_url = "https://res.cloudinary.com/demo/image/upload/sample.jpg"
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                    urllib.request.urlretrieve(demo_url, tmp.name)
                    tmp_path = tmp.name

                # Wrap in a Django-compatible file-like object for the upload utility
                class FakeUploadedFile:
                    def __init__(self, path):
                        self._file = open(path, 'rb')
                        self.content_type = 'image/jpeg'
                        self.size = os.path.getsize(path)
                        self.name = 'seed_placeholder.jpg'

                    def read(self, size=-1):
                        return self._file.read(size)

                    def seek(self, pos):
                        return self._file.seek(pos)

                    def tell(self):
                        return self._file.tell()

                    def close(self):
                        self._file.close()

                fake_file = FakeUploadedFile(tmp_path)
                result = upload_product_image(fake_file, "seed-placeholder")
                fake_file.close()
                os.unlink(tmp_path)

                cloudinary_seed_url = result["url"]
                self.stdout.write(self.style.SUCCESS(f"   ✅ Uploaded: {cloudinary_seed_url}"))

            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f"   ⚠ Cloudinary upload failed: {e}. Falling back to placeholder URL."
                ))
                cloudinary_seed_url = None

        # Decide which image URL to use for all seeded products
        seed_image_url = cloudinary_seed_url if cloudinary_seed_url else PLACEHOLDER_IMAGE

        # ── Step 4: Create products ────────────────────────────────────────
        self.stdout.write(f"📦  Creating {len(PRODUCTS_DATA)} products...")
        created_count = 0

        for data in PRODUCTS_DATA:
            cat_slug = data["category"]
            category = category_map.get(cat_slug)
            if not category:
                self.stdout.write(self.style.WARNING(
                    f"   ⚠ Category not found: {cat_slug}, skipping {data['name']}"
                ))
                continue

            slug = Product.generate_unique_slug(data["name"])

            if Product.objects(slug=slug).first():
                self.stdout.write(f"   ⏭  Already exists: {data['name']}")
                continue

            variants = []
            for v in data["variants"]:
                variant = Variant(
                    variant_id=str(uuid.uuid4()),
                    size=v.get("size"),
                    color=v.get("color"),
                    sku=v["sku"],
                    price=v["price"],
                    stock=v["stock"],
                    images=[],
                )
                variants.append(variant)

            avg_rating   = round(random.uniform(3.5, 5.0), 1)
            review_count = random.randint(0, 200)
            days_ago     = random.randint(0, 90)
            created_at   = datetime.utcnow() - timedelta(days=days_ago)

            product = Product(
                seller_id=seller_id,
                category_id=category.id,
                name=data["name"],
                slug=slug,
                description=data["description"],
                brand=data.get("brand", ""),
                base_price=data["base_price"],
                images=[seed_image_url],
                tags=data.get("tags", []),
                variants=variants,
                avg_rating=avg_rating,
                review_count=review_count,
                is_active=True,
                created_at=created_at,
                updated_at=created_at,
            )
            product.save()
            created_count += 1
            self.stdout.write(f"   ✅ {data['name']} ({cat_slug})")

        self.stdout.write(self.style.SUCCESS(
            f"\n🎉  Done! Created {len(CATEGORIES)} categories and {created_count} products."
        ))
        self.stdout.write(
            "   Tip: run with --use-cloudinary to upload real images to Cloudinary."
        )