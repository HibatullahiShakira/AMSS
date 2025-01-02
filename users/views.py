from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import Group
from rest_framework_simplejwt.models import TokenUser
from djoser.views import UserViewSet
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
        self.check_permissions(request)

        if isinstance(request.user, TokenUser):
            user = User.objects.get(id=request.user.id)
        else:
            user = request.user

        user_data = request.data.copy()

        if user.business:
            user_data['business_id'] = user.business.id
        else:
            return Response({"detail": "Authenticated user does not belong to any business."},
                            status=status.HTTP_400_BAD_REQUEST)

        user_serializer = self.get_serializer(data=user_data, context={'request': request})
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        return JsonResponse(user_serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        self.check_permissions(request)

        if isinstance(request.user, TokenUser):
            user = User.objects.get(id=request.user.id)
        else:
            user = request.user

        if not hasattr(user, 'business') or not user.business:
            return Response({"detail": "Authenticated user does not belong to any business."},
                            status=status.HTTP_400_BAD_REQUEST)

        queryset = User.objects.filter(business=user.business)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        self.check_permissions(request)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self.check_permissions(request)
        return super().destroy(request, *args, **kwargs)


class CustomUserViewSet(UserViewSet):
    def me(self, request, *args, **kwargs):
        user = request.user
        print(f"Request User: {user}")
        if not user:
            return Response({"detail": "User instance is None"}, status=status.HTTP_400_BAD_REQUEST)
        print(f"User ID: {user.id}, Username: {user.username}, Email: {user.email}")

        response = super().update(request, *args, **kwargs)
        print(f"Response Data: {response.data}")
        return response
