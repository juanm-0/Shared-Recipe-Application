from rest_framework.permissions import BasePermission


def is_owner_or_staff(user, obj):
    """Object-level permission for resources that are publicly visible but
    owner-restricted for writes (e.g. Recipe, Review).

    Not for shopping lists where a non-owner should get 404 rather than 403
    (exists but forbidden) need queryset-scoping instead.
    """
    if user.is_staff:
        return True
    owner = getattr(obj, "owner", None) or getattr(obj, "user", None)
    return owner == user


class IsOwnerOrStaff(BasePermission):
    def has_object_permission(self, request, view, obj):
        return is_owner_or_staff(request.user, obj)
