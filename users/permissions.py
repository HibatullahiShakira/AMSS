from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.models import TokenUser
from .models import User


class IsOwner(BasePermission):
    def has_permission(self, request, view):
        if isinstance(request.user, TokenUser):
            print(f"TokenUser detected: {request.user}")
            user = User.objects.get(id=request.user.id)
            print(f"Converted TokenUser to User: {user.username}")
        else:
            user = request.user

        has_perm = user.groups.filter(name='Owner').exists()
        print(f"User {user.username} has 'Owner' permission: {has_perm}")
        if not has_perm:
            print(f"Permission denied for user {user.username} in view {view.__class__.__name__}")
        return has_perm

    def has_object_permission(self, request, view, obj):
        if isinstance(request.user, TokenUser):
            print(f"TokenUser detected: {request.user}")
            user = User.objects.get(id=request.user.id)
            print(f"Converted TokenUser to User: {user.username}")
        else:
            user = request.user

        if hasattr(user, 'business') and user.business == obj.business:
            has_obj_perm = user.groups.filter(name='Owner').exists()
            print(
                f"User {user.username} has object-level 'Owner' permission for business {obj.business}: {has_obj_perm}")
            if not has_obj_perm:
                print(f"Object-level permission denied for user {user.username} for business {obj.business}")
            return has_obj_perm
        print(f"User {user.username} does not have object-level permission for business {obj.business}")
        return False
