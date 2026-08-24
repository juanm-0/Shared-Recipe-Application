from rest_framework.permissions import BasePermission

ACTION_BY_METHOD = {
    "DELETE": "delete",
}


def is_owner_or_has_permission(user, obj, action="change"):
    owner = getattr(obj, "owner", None) or getattr(obj, "user", None)
    if owner == user:
        return True
    return user.has_perm(f"{obj._meta.app_label}.{action}_{obj._meta.model_name}")


class IsOwnerOrHasPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        action = ACTION_BY_METHOD.get(request.method, "change")
        return is_owner_or_has_permission(request.user, obj, action=action)
