from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser, Permission, Group


class UserRole(models.Model):
    ROLE_CHOICE = [
        ('ADMIN', 'admin'),
        ('EMPLOYEE', 'employee'),
        ('OWNER', 'owner'),
        ('MANAGER', 'manager'),
        ('ACCOUNTANT', 'manager')
    ]

    name = models.CharField(max_length=50, choices=ROLE_CHOICE)
    role_description = models.TextField()

    def __str__(self):
        return self.name


class Business(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name='business_profile')
    business_name = models.CharField(max_length=255, unique=True)
    business_address = models.CharField(max_length=255)
    business_type = models.CharField(max_length=100)
    bank_account_details = models.CharField(max_length=255, blank=True, null=True)
    preferred_currency = models.CharField(max_length=50, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    annual_revenue = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    business_email = models.EmailField(max_length=254)
    # is_verified = models.BooleanField(default=False)
    # verification_token = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return self.business_name

    # def generate_verification_token(self):
    #     self.verification_token = str(random.randint(100000, 999999))
    #     self.save()
    #     return self.verification_token
    #
    # def verify_token(self, token):
    #     return self.verification_token == token


class UserBusiness(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,  on_delete=models.CASCADE)
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    role = models.ForeignKey(UserRole, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.user} - {self.business} - {self.role}"


class User(AbstractUser):
    email = models.EmailField(unique=True)
    roles = models.ManyToManyField(UserRole, through='UserBusiness')
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='staff_members', null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    groups = models.ManyToManyField(Group, related_name='custom_user_set')
    user_permissions = models.ManyToManyField(Permission, related_name='custom_user_set_permissions')

    @classmethod
    def get_with_business(cls, user_id):
        return cls.objects.select_related('business').get(id=user_id)
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username
