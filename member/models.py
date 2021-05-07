from django.db import models

class Member(models.Model):
    major = models.CharField(max_length=20, null=False)
    stdnum = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=10, null=False)
    email = models.EmailField(max_length=100, unique=True)
    email_hash = models.CharField(max_length=200, unique=False, null=True)
    image = models.CharField(max_length=100, unique=True, null=True)
