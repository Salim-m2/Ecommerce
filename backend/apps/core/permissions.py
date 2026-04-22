"""
Shared DRF permission classes used across multiple apps.

Why live in core/?
Permission classes are reused by products, orders, and reviews apps.
Defining them in one place avoids circular imports and keeps each app
focused on its own domain.
"""
from rest_framework.permissions import BasePermission


class IsAdminOrSeller(BasePermission):
    """
    Grants access only to authenticated users whose role is 'admin' or 'seller'.

    Used for:
    - POST /api/v1/products/upload-image/   (upload product images)
    - POST /api/v1/products/                (create products, Week 9)
    - PUT  /api/v1/products/{slug}/         (update products, Week 9)

    Why check both role AND is_authenticated?
    BasePermission.has_permission is called before any view logic runs.
    If request.user is an AnonymousUser, accessing .role would raise an
    AttributeError. The is_authenticated guard prevents that.
    """
    message = "You must be an admin or seller to perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'role')
            and request.user.role in ('admin', 'seller')
        )


class IsAdmin(BasePermission):
    """
    Grants access only to authenticated users whose role is 'admin'.

    Used for:
    - PATCH /api/v1/orders/{order_number}/status/   (Week 7)
    - GET   /api/v1/admin/orders/                   (Week 7)
    - DELETE /api/v1/products/{slug}/               (Week 9)
    """
    message = "You must be an admin to perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'role')
            and request.user.role == 'admin'
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission: grants access if the requesting user owns
    the object OR is an admin.

    Used for:
    - DELETE /api/v1/reviews/{id}/   (Week 7) — user can delete their own review
    - GET    /api/v1/orders/{number}/ (Week 7) — user can only view their own orders

    The view must call self.check_object_permissions(request, obj) for this
    to be evaluated — has_object_permission is not called automatically.
    """
    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == 'admin':
            return True
        # The object must have a user_id field pointing to the owner
        owner_id = getattr(obj, 'user_id', None)
        return owner_id and str(owner_id) == str(request.user.id)