from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BusinessViewSet

router = DefaultRouter()
router.register(r'business', BusinessViewSet, basename='business')

urlpatterns = [
    # path('auth/', include('djoser.urls')),
    # path('auth/', include('djoser.urls.jwt')),  # For JWT
    path('', include(router.urls)),
]
