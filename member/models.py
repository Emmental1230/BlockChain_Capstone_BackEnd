from django.db import models

class Member(models.Model):
    email = models.EmailField(max_length=100, primary_key=True)
    info_hash = models.CharField(max_length=200, null=True)
    user_key = models.CharField(max_length=200, unique=False, null=True)
    wallet_id = models.CharField(max_length=200, unique=False, null=True)
    wallet_key = models.CharField(max_length=30, null=True)
    did = models.CharField(max_length=200, unique=False, null=True)
    did_time_hash =  models.CharField(max_length=200, unique=False, null=True)

class Entry(models.Model) :
    entry_date = models.CharField(max_length=50, null=True)
    building_num = models.CharField(max_length=30, null=True)
    entry_did = models.CharField(max_length=100, null=True)
