from rest_framework.permissions import BasePermission


class IsOwnerOrStaff(BasePermission):
    """Object-level permission for resources that are publicly visible but
    owner-restricted for writes (e.g. Recipe, Review).

    Not for shopping lists where a non-owner should get 404 rather than 403
    (exists but forbidden) need queryset-scoping instead.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        owner = getattr(obj, "owner", None) or getattr(obj, "user", None)
        return owner == request.user
