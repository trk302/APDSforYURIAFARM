from django.contrib.auth.models import AbstractUser
from django.db import models
from .managers import CustomUserManager

class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Role(models.TextChoices):
    EMPLOYEE = 'employee', 'Працівник'
    MANAGER = 'manager', 'Керівник'
    ADMIN = 'admin', 'Адміністратор'

class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(unique=True, verbose_name="Електронна пошта")

    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    position = models.CharField(max_length=100)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.EMPLOYEE)
    photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'phone_number', 'position']

    objects = CustomUserManager()

    def __str__(self):
        return self.email
