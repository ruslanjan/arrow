from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
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

    def get_duration_minutes(self):
        return self.duration / 60

    def get_duration_hours(self):
        return self.duration / 3600

    def get_time_till_start(self):
        return self.start_date_time - timezone.now()

    def get_datetime_till_end(self):
        return self.start_date_time + timezone.timedelta(
            seconds=self.duration) - timezone.now()

    def get_end_datetime(self):
        return self.start_date_time + timezone.timedelta(seconds=self.duration)

    def get_tasks(self):
        return self.contesttask_set.order_by('index')


class ContestTask(IndexedModel):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=256)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, null=True)


class ContestUserProfile(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, null=False)
    points = models.FloatField(default=0)
    solved_count = models.IntegerField(default=0)
    penalty = models.FloatField(default=0)
    solved_count_after_contest = models.IntegerField(default=0)
    points_after_contest = models.FloatField(default=0)

    def get_task_profiles(self):
        if self.contestusertaskprofile_set.count() != self.contest.contesttask_set.count():
            for task in self.contest.contesttask_set.exclude(
                id__in=self.contestusertaskprofile_set.values_list('id',
                                                                   flat=True)):
                contest_user_task_profile = ContestUserTaskProfile(
                    task=task,
                    contest=self.contest,
                    user_profile=self)
                contest_user_task_profile.save()
        return self.contestusertaskprofile_set.order_by('task__index')

    def get_solved_count(self):
        return self.solved_count

    def get_solved_count_after_contest_count(self):
        return self.solved_count_after_contest


class ContestUserTaskProfile(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_profile = models.ForeignKey(ContestUserProfile,
                                     on_delete=models.CASCADE,
                                     null=False)
    task = models.ForeignKey(ContestTask, on_delete=models.CASCADE)
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, null=False)
    points = models.FloatField(default=0)
    solved = models.BooleanField(default=False)
    tries = models.IntegerField(default=0)
    penalty = models.FloatField(default=0)
    solved_after_contest = models.BooleanField(default=False)
    tries_after_contest = models.IntegerField(default=0)
    points_after_contest = models.FloatField(default=0)


class ContestUserSubmission(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, null=False)
    user_profile = models.ForeignKey(ContestUserProfile,
                                     on_delete=models.CASCADE,
                                     null=False)
    user_task_profile = models.ForeignKey(ContestUserTaskProfile,
                                          on_delete=models.CASCADE,
                                          null=False)
    task = models.ForeignKey(ContestTask, on_delete=models.CASCADE,
                             null=False)
    upsolving = models.BooleanField(default=False)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE,
                                   null=False)
