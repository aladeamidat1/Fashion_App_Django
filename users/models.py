from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class User(AbstractUser):
    is_Designer = models.BooleanField(default=False)
    is_Customer = models.BooleanField(default=False)
    phone = models.CharField(max_length=11 , unique=True)
    email = models.EmailField(unique=True)


