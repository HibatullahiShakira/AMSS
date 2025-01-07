from rest_framework import permissions
from rest_framework_simplejwt.models import TokenUser
from users.models import User


class IsOwnerAdminManagerOrReadonly(permissions.BasePermission):
    def has_permission(self, request, view):
        if isinstance(request.user, TokenUser):
            print(f"TokenUser detected: {request.user}")
            user = User.objects.get(id=request.user.id)
            print(f"Converted TokenUser to User: {user.username}")
        else:
            user = request.user

        user_groups = list(user.groups.values_list('name', flat=True))
        print(f"Checking general permission for user: {user}, groups: {user_groups}, method: {request.method}")

        if request.method in permissions.SAFE_METHODS:
            return user and user.is_authenticated

        has_permission = (
                user and user.is_authenticated and
                (
                        'Admin' in user_groups or
                        'Owner' in user_groups or
                        'Manager' in user_groups or
                        user.is_superuser
                )
        )

        print(f"General permission result for user {user.username}: {has_permission}")
        return has_permission

    def has_object_permission(self, request, view, obj):
        if isinstance(request.user, TokenUser):
            print(f"TokenUser detected: {request.user}")
            user = User.objects.get(id=request.user.id)
            print(f"Converted TokenUser to User: {user.username}")
        else:
            user = request.user

        user_groups = list(user.groups.values_list('name', flat=True))
        print(
            f"Checking object permission for user: {user}, groups: {user_groups}, obj user: {obj.user}, method: {request.method}")

        if request.method in permissions.SAFE_METHODS:
            return True

        has_obj_permission = (
                obj.user == user or
                'Admin' in user_groups or
                'Owner' in user_groups or
                'Manager' in user_groups or
                user.is_superuser
        )
        print(f"Object permission result for user {user.username}: {has_obj_permission}")

        return has_obj_permission


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if isinstance(request.user, TokenUser):
            print(f"TokenUser detected: {request.user}")
            user = User.objects.get(id=request.user.id)
            print(f"Converted TokenUser to User: {user.username}")
        else:
            user = request.user

        user_groups = list(user.groups.values_list('name', flat=True))
        print(f"Checking general permission for user: {user}, groups: {user_groups}, method: {request.method}")

        has_permission = user and user.is_authenticated and (
                'Admin' in user_groups or 'Owner' in user_groups or user.is_superuser
        )

        print(f"General permission result for user {user.username}: {has_permission}")
        return has_permission

    def has_object_permission(self, request, view, obj):
        if isinstance(request.user, TokenUser):
            print(f"TokenUser detected: {request.user}")
            user = User.objects.get(id=request.user.id)
            print(f"Converted TokenUser to User: {user.username}")
        else:
            user = request.user

        user_groups = list(user.groups.values_list('name', flat=True))
        print(f"Checking object permission for user: {user}, groups: {user_groups}, obj user: {obj.user}, method: {request.method}")

        has_obj_permission = 'Admin' in user_groups or 'Owner' in user_groups or user.is_superuser
        print(f"Object permission result for user {user.username}: {has_obj_permission}")

        return has_obj_permission

