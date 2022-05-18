from django.db import models
from django.forms import PasswordInput
from django.utils.timezone import now
from datetime import timedelta

from pandas import notnull

class users(models.Model):
    username = models.CharField(max_length=25, default='')
    password = models.CharField(max_length=50)
    createdate = models.DateTimeField(default=now)
    status = models.IntegerField()
    salt = models.CharField(max_length=25, default='')
    profile_type = models.IntegerField(null=0)
    email = models.EmailField(max_length=50)
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=50)
    last_login = models.DateTimeField(null=True)
    expire_pwd = models.DateTimeField(default=(now() + timedelta(90)))
    ip = models.CharField(max_length=25, default='')
    session_key = models.CharField(max_length=100 , default='')


class user_log(models.Model):
    id_user = models.ForeignKey(users,related_name='id_user', on_delete=models.CASCADE)
    task = models.CharField(max_length=200)
    dateof = models.DateTimeField(default=now)
    ip = models.CharField(max_length=25, default='')
    session_key = models.CharField(max_length=100 , default='')
    description = models.CharField(max_length=200, default='')

class login_log(models.Model):
    username = users.username.field
    dateof = models.DateTimeField(default=now)
    auth = models.IntegerField()
    ip = models.CharField(max_length=25, default='')
    session_key = models.CharField(max_length=100 , default='')