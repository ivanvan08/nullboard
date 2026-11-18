from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminUserOrReadOnly(BasePermission):
    """
    Allows read access to any request (GET, HEAD, OPTIONS).
    Write access (POST, PUT, PATCH, DELETE) is only allowed to staff / admin users.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsAuthenticatedOrReadOnly(BasePermission):
    """
    Allows read access to any request.
    Write access requires an authenticated user.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)
