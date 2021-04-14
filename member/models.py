from django.db import models

class Member(models.Model):
    major = models.CharField(max_length=200, null=False)
    stdnum = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=200, null=False)
    email = models.EmailField(max_length=500, unique=True)