from django.db import models

class Member(models.Model):
    email = models.EmailField(max_length=100, primary_key=True)
    user_key = models.CharField(max_length=200, unique=False, null=True)
