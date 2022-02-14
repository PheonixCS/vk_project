from django.db import models


class AuthCode(models.Model):
    code = models.CharField(max_length=8, null=False, default='', blank=True)
    user = models.ForeignKey('posting.User', on_delete=models.CASCADE)
    create_dt = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)
