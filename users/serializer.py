from rest_framework import serializers
from rest_framework_simplejwt.models import TokenUser
from django.contrib.auth.models import Group
from djoser.serializers import UserSerializer as DjoserUserSerializer
from .models import Business, User


class BusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = '__all__'

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request and not request.user.is_anonymous else None

        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = Business.objects.create(user=user, **validated_data)
        return business


class CustomUpdateBusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ['name', 'description', 'address', 'phone', 'email']  # Include all relevant fields

    def update(self, instance, validated_data):
        user = self.context['request'].user
        instance.user = user
        instance.business = user.business

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class BusinessStaffSerializer(DjoserUserSerializer):
    role = serializers.CharField(write_only=True)
    user_role = serializers.SerializerMethodField()
    phone_number = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    age = serializers.IntegerField(required=True)
    business_id = serializers.PrimaryKeyRelatedField(queryset=Business.objects.all(), write_only=True)
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + (
            'username', 'first_name', 'last_name', 'role', 'business_id', 'phone_number', 'address', 'age', 'user_role',
            'password')

    def get_user_role(self, obj):
        roles = obj.groups.values_list('name', flat=True)
        return list(roles)

    def create(self, validated_data):
        role = validated_data.pop('role', None)
        business = validated_data.pop('business_id', None)
        password = validated_data.pop('password', None)

        if not validated_data.get('username'):
            raise serializers.ValidationError({"username": "This field is required."})

        if User.objects.filter(username=validated_data['username']).exists():
            raise serializers.ValidationError({"username": "This username is already taken."})

        user = User.objects.create(**validated_data)
        user.set_password(password)

        if business:
            user.business = business

        if role:
            group, created = Group.objects.get_or_create(name=role)
            user.groups.add(group)

        user.save()
        return user
