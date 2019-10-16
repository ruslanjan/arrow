from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from problemset.models import ProblemsetUserProfile


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=16, blank=True)
    problemset_profile = models.ForeignKey(ProblemsetUserProfile,
                                           null=True,
                                           on_delete=models.SET_NULL,
                                           blank=True)

    def __str__(self):
        return self.user.username + ' | ' + self.user.get_full_name()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
