from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Post(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="user_post")
    description = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True, null=False)
    likes = models.ManyToManyField('User')


class Follow(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="user_follow")
    following = models.ForeignKey("User", on_delete=models.CASCADE, related_name="following_follow")