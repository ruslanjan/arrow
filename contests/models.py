from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
import datetime

from polygon.models import Problem, Submission
from utils import IndexedModel


class Contest(models.Model):
    """
    So this is a bit complicated.
    During set up and other stuff nothing really happens beside data updates.

    However when admin pushes launch button it sets is_launched to True
    and then celery task will check every second
    if there is a contest that should start now or end now.

    Admin can switch contest to manual mode. Then celery scheduler won't touch
    it. But for users start_date_time, end_date_time and duration will be shown
    and can lead to negative time but this is expected. In manual control
    contest should be started and ended manually.
    """
    name = models.CharField(max_length=256, unique=True)
    is_ioi_style = models.BooleanField(max_length=256, default=False)
    start_date_time = models.DateTimeField(default=timezone.now)
    duration = models.IntegerField(default=7200)  # in seconds
    # end_date_time = models.DateTimeField(default=None, null=True)
    is_started = models.BooleanField(default=False)
    is_ended = models.BooleanField(default=False)
    manual_control = models.BooleanField(default=False)
    is_launched = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)


class ContestTask(IndexedModel):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=256)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, null=True)


class ContestUserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, null=False)


class ContestUserTaskProfile(models.Model):
    contest_user_profile = models.ForeignKey(ContestUserProfile,
                                             on_delete=models.CASCADE,
                                             null=False)
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, null=False)
    points = models.FloatField(default=0)
    solved = models.BooleanField(default=False)
    tries = models.IntegerField(default=0)
    penalty = models.IntegerField(default=0)


class ContestUserSubmission(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, null=False)
    contest_user_profile = models.ForeignKey(ContestUserProfile,
                                             on_delete=models.CASCADE,
                                             null=False)
    contest_user_task_profile = models.ForeignKey(ContestUserTaskProfile,
                                                  on_delete=models.CASCADE,
                                                  null=False)
    contest_task = models.ForeignKey(ContestTask, on_delete=models.CASCADE,
                                     null=False)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE,
                                   null=False)
