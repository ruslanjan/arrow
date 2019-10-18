from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from polygon.models import Problem, Submission


class ProblemsetTask(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    problem = models.ForeignKey(Problem, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=128, unique=True)
    is_active = models.BooleanField(default=False)

    def count_user_solved(self):
        return self.problemsetusertaskprofile_set.filter(
            solved=True).count()

    def __str__(self):
        return f'{self.name}'


class ProblemsetUserProfile(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f'{self.user}'


@receiver(post_save, sender=User)
def create_problemset_user_profile(sender, instance, created, **kwargs):
    if created:
        ProblemsetUserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_problemset_user_profile(sender, instance: User, **kwargs):
    instance.problemsetuserprofile.save()


class ProblemsetUserTaskProfile(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    problemset_task = models.ForeignKey(ProblemsetTask,
                                        on_delete=models.CASCADE, null=False)
    user_profile = models.ForeignKey(ProblemsetUserProfile,
                                     on_delete=models.CASCADE, null=True)
    tried_count = models.IntegerField(default=0)
    # bad_tried_count = models.IntegerField(default=0)
    solved = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.problemset_task} | {self.user_profile}'


class ProblemsetSubmission(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    problemset_task = models.ForeignKey(ProblemsetTask,
                                        on_delete=models.CASCADE, null=False)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE,
                                   null=False)
    user_profile = models.ForeignKey(ProblemsetUserProfile,
                                     on_delete=models.CASCADE,
                                     null=False)
    user_task_profile = models.ForeignKey(ProblemsetUserTaskProfile,
                                          on_delete=models.CASCADE,
                                          null=False)

    def __str__(self):
        return f'{self.pk} on task {self.problemset_task}'
