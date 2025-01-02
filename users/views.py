from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import Group
from rest_framework_simplejwt.models import TokenUser

from .models import Business, User
from .permissions import IsOwner
from .serializer import BusinessSerializer, BusinessStaffSerializer


class BusinessRegistrationView(viewsets.ModelViewSet):
    queryset = Business.objects.all()
    serializer_class = BusinessSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        business_data = request.data
        business_serializer = self.get_serializer(data=business_data, context={'request': request})
        business_serializer.is_valid(raise_exception=True)

        business = business_serializer.save()

        user = User.objects.get(id=request.user.id)
        print(f"Retrieved user object: {user}")

        if not hasattr(user, 'groups'):
            return Response({"detail": "User does not have groups attribute."}, status=status.HTTP_400_BAD_REQUEST)

        owner_group, created = Group.objects.get_or_create(name='Owner')
        user.groups.add(owner_group)
        user.business = business
        user.save()

        return JsonResponse(business_serializer.data, status=status.HTTP_201_CREATED)


class BusinessStaffRegistrationView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = BusinessStaffSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def create(self, request, *args, **kwargs):
        if isinstance(request.user, TokenUser):
            print(f"TokenUser detected: {request.user}")
            user = User.objects.get(id=request.user.id)
            print(f"Converted TokenUser to User: {user.username}")
        else:
            user = request.user

        print(f"Authenticated user: {user}")
        print(f"Authenticated user ID: {user.id if hasattr(user, 'id') else 'No ID'}")
        print(f"Authenticated user groups: {user.groups.all() if hasattr(user, 'groups') else 'No groups'}")

        user_data = request.data.copy()

        if user.business:
            user_data['business_id'] = user.business.id
        else:
            return Response({"detail": "Authenticated user does not belong to any business."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Ensure the context is passed to the serializer
        user_serializer = self.get_serializer(data=user_data, context={'request': request})
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        return Response(user_serializer.data, status=status.HTTP_201_CREATED)
