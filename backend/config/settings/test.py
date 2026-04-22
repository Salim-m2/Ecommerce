from .dev import *

# Use a completely separate MongoDB database for tests.
# This database is wiped and recreated on every test run.
# It never touches ecommerce_db.
import mongoengine

# Disconnect the dev connection first
mongoengine.disconnect(alias='default')

# Reconnect to the test database
mongoengine.connect(
    db='ecommerce_test_db',
    host=env('MONGO_URI'),
    alias='default',
)

# Ensure indexes exist on the TEST database.
# base.py already called create_product_indexes() against the dev DB before
# we reconnected here, so we must call it again for ecommerce_test_db.
from apps.products.indexes import create_product_indexes
create_product_indexes()