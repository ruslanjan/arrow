from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count

from polygon.models import Problem, Submission


class ProblemsetTask(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    problem = models.ForeignKey(Problem, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=128, unique=True)
    is_active = models.BooleanField(default=False)

    def count_user_solved(self):
        return self.problemsetsubmission_set.filter(
            submission__verdict=Submission.OK,
            submission__tested=True).aggregate(
            count=Count("user_profile", distinct=True))['count']

    def __str__(self):
        return f'{self.name}'


class ProblemsetUserProfile(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tasks_solved = models.ManyToManyField(ProblemsetTask)
    tasks_tried = models.ManyToManyField(ProblemsetTask,
                                         related_name='tasks_tried')
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f'{self.user}'


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

    def __str__(self):
        return f'{self.pk} on task {self.problemset_task}'
