from .dev import *
import mongoengine

# Disconnect the dev connection established in base.py
mongoengine.disconnect(alias='default')

# Reconnect to the isolated test database — never touches ecommerce_db
mongoengine.connect(
    db='ecommerce_test_db',
    host=env('MONGO_URI'),
    alias='default',
)

# Re-run index creation against the test database
from apps.products.indexes import create_product_indexes
create_product_indexes()