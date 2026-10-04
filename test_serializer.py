import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AMS.settings')
django.setup()

from users.models import User
from users.serializers import CustomUserSerializer

user = User.objects.get(username="testuser")
serializer = CustomUserSerializer(user)
print("Serializer Data:", serializer.data)
print("User business ID:", user.business_id)
