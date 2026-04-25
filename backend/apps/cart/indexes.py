# from apps.cart.documents import Cart


# def create_cart_indexes():
#     """
#     Ensures the required indexes exist on the carts collection.
#     Called once at startup from settings/base.py after the mongoengine connection.

#     sparse=True on user_id and session_key means MongoDB skips null values in
#     those indexes — without sparse, every guest cart would count against the
#     user_id index as a duplicate null, which would break a unique constraint.
#     """
#     collection = Cart._get_collection()

#     # user_id — for fast lookup of a logged-in user's cart
#     collection.create_index(
#         [('user_id', 1)],
#         sparse=True,
#         name='cart_user_id_sparse'
#     )

#     # session_key — for fast lookup of a guest cart
#     collection.create_index(
#         [('session_key', 1)],
#         sparse=True,
#         name='cart_session_key_sparse'
#     )

#     # updated_at desc — useful for a future cron job that cleans up
#     # abandoned guest carts older than X days
#     collection.create_index(
#         [('updated_at', -1)],
#         name='cart_updated_at_desc'
#     )

#     print('✓ Cart indexes ensured.')