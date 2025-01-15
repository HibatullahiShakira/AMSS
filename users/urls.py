from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BusinessRegistrationView, BusinessStaffRegistrationView

router = DefaultRouter()
router.register(r'business', BusinessRegistrationView, basename='business')
router.register(r'register-business-staff', BusinessStaffRegistrationView, basename='register-business-staff')

urlpatterns = [
    path('', include(router.urls)),
]
