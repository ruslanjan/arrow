from django.contrib.auth.models import User
from django.db import models

from polygon.models import Problem, TestGroup, Test


class Submission(models.Model):
    CPP17 = 'CPP17'
    PYTHON3 = 'PYTHON3.7'

    SUBMISSION_TYPES = (
        (CPP17, 'gcc C++ 17'),
        (PYTHON3, 'python 3.7'),
    )

    # These are returns code from checker (testlib.h). at line 203
    OK = 'OK'  # return code 0
    WA = 'WA'  # return code 1
    PE = 'PE'  # return code 2
    TF = 'TF'  # return code 3
    POINTS = 'PTS'  # return code 7. Only for problems is_graded or is_sub_task.

    UNEXPECTED_EOF = 'EOF'  # code 8
    UNKNOWN_CODE = 'UC'
    TE = 'TE'
    TLE = 'TLE'
    MLE = 'MLE'
    RE = 'RE'
    CP = 'CP'
    WTL = 'WTE'

    VERDICT_TYPES = (
        (OK, 'OK'),
        (WA, 'Wrong answer'),
        (PE, 'Presentation error'),
        (UNEXPECTED_EOF, 'UNEXPECTED_EOF'),
        (TLE, 'Time limit exceeded'),
        (MLE, 'Memory limit exceeded'),
        (RE, 'Runtime error'),
        (CP, 'Compilation Error'),
        (TE, 'Test error'),
        (WTL, 'Test error'),
        (UNKNOWN_CODE, 'Unknown code'),
        (POINTS, 'POINTS'),
    )

    def erase_verdict(self):
        self.submissiontestresult_set.all().delete()
        self.submissiontestgroupresult_set.all().delete()
        self.verdict = ''
        self.verdict_message = ''
        self.verdict_debug_description = ''
        self.verdict_debug_message = ''
        self.verdict_description = ''
        self.testing_message = 'Testing'
        self.tested = False
        self.testing = False
        self.max_time_used = -1
        self.max_memory_used = -1
        self.in_queue = False

    def get_verdict(self):
        if self.tested:
            return self.verdict_message
        if self.testing:
            if self.testing_message:
                return self.testing_message
            else:
                return 'Testing'
        if self.in_queue:
            return 'In queue'
        return 'Not in queue'

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    data = models.TextField(blank=True)
    points = models.FloatField(default=0)
    in_queue = models.BooleanField(default=False)
    tested = models.BooleanField(default=False)
    testing = models.BooleanField(default=False)
    testing_message = models.CharField(default='Testing', blank=True,
                                       max_length=256)
    max_time_used = models.FloatField(default=-1)
    max_memory_used = models.IntegerField(default=-1)
    verdict_message = models.CharField(default='', max_length=256)
    verdict_description = models.TextField(default='')
    verdict_debug_message = models.CharField(default='', max_length=256)
    verdict_debug_description = models.TextField(default='')
    verdict = models.CharField(choices=VERDICT_TYPES,
                               blank=True,
                               max_length=64,
                               default=None,
                               null=True)
    submission_type = models.CharField(choices=SUBMISSION_TYPES,
                                       max_length=64,
                                       null=False,
                                       blank=False)

    def __str__(self):
        return f'Problem: {self.problem.name} | Submission: {self.pk}'


class SubmissionTestGroupResult(models.Model):
    test_group = models.ForeignKey(TestGroup, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    points = models.FloatField(default=0)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE,
                                   null=False)


# to get better description on individual test and to count points for
# problems is_graded or is_sub_task
class SubmissionTestResult(models.Model):
    OK = 'OK'  # return code 0
    WA = 'WA'  # return code 1
    PE = 'PE'  # return code 2
    TF = 'TF'  # return code 3
    POINTS = 'PTS'  # return code 7

    UNEXPECTED_EOF = 'EOF'  # code 8
    UNKNOWN_CODE = 'UC'
    TE = 'TE'
    WTL = 'WTE'
    TLE = 'TLE'
    MLE = 'MLE'
    RE = 'RE'

    VERDICT_TYPES = (
        (OK, 'OK'),
        (WA, 'Wrong answer'),
        (PE, 'Presentation error'),
        (UNEXPECTED_EOF, 'Unexpected EOF'),
        (TLE, 'Time limit exceeded'),
        (MLE, 'Memory limit exceeded'),
        (RE, 'Runtime error'),
        (TE, 'Test error'),
        (WTL, 'WTE'),
        (UNKNOWN_CODE, 'Unknown code'),
        (POINTS, 'POINTS'),
    )

    submission = models.ForeignKey(Submission, on_delete=models.CASCADE,
                                   null=False)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, null=False)
    test_group_result = models.ForeignKey(SubmissionTestGroupResult,
                                          on_delete=models.SET_NULL, null=True,
                                          blank=True)
    points = models.FloatField(default=0)
    time_used = models.FloatField(default=-1)
    memory_used = models.IntegerField(default=-1)
    verdict_message = models.CharField(default='', max_length=256)
    verdict_description = models.TextField(default='')
    verdict_debug_message = models.CharField(default='', max_length=256)
    verdict_debug_description = models.TextField(default='')
    verdict = models.CharField(choices=VERDICT_TYPES,
                               blank=True,
                               max_length=64,
                               default=None,
                               null=True)