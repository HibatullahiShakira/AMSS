from djoser.serializers import UserSerializer as BaseUserSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

class CustomUserSerializer(BaseUserSerializer):
    business = serializers.SerializerMethodField()
    
    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = tuple(BaseUserSerializer.Meta.fields) + ('business',)
        
    def get_business(self, obj):
        return obj.business_id
