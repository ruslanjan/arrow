import os
import secrets

from django.contrib.auth.models import User
from django.db import models
# Problem related models
from django.db.models.signals import post_delete
from django.dispatch import receiver


class Problem(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=128, unique=True)
    time_limit = models.FloatField(default=1)
    memory_limit = models.IntegerField(default=256000)
    is_interactive = models.BooleanField(default=False)
    solution = models.TextField(blank=True)
    checker = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)
    test_generator_script = models.TextField(blank=True, default="")

    def get_example_tests(self):
        return self.test_set.filter(is_example=True)

    def __str__(self):
        return str(self.pk) + ' | ' + self.name + ' | ' + str(self.is_active)


def get_statement_folder(instance, filename):
    return f'problem/{instance.problem.pk}/statement/{instance.pk}/{filename}'


def get__problem_file_folder(instance, filename):
    secrets.token_hex(4)
    filename = f'{filename[:filename.rfind(".")]}_{secrets.token_hex(4)}{filename[filename.rfind("."):]}'
    return f'problem/{instance.problem.pk}/files/{filename}'


class ProblemFile(models.Model):
    problem = models.ForeignKey(
        Problem, blank=True, null=False, on_delete=models.CASCADE)
    file = models.FileField(upload_to=get__problem_file_folder)

    def filename(self):
        return os.path.basename(self.file.name)

    def __str__(self):
        return f'{self.problem} | {self.file}'


@receiver(post_delete, sender=ProblemFile)
def submission_delete(sender, instance: ProblemFile, **kwargs):
    instance.file.delete(False)


class Statement(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=64, default='Statement')
    is_visible = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)
    only_pdf = models.BooleanField(default=False)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    pdf_statement = models.FileField(upload_to=get_statement_folder, blank=True,
                                     null=True)
    problem_name = models.CharField(max_length=256, default='')
    legend = models.TextField(blank=True, default='')
    input_format = models.TextField(blank=True, default='')
    output_format = models.TextField(blank=True, default='')
    notes = models.TextField(blank=True, default='')

    # legend = models.TextField(blank=True)
    # input_format = models.TextField(blank=True)
    # output_format = models.TextField(blank=True)
    def __str__(self):
        return self.problem.name + ' | ' + self.name


class Generator(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=64)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    generator = models.TextField()

    def __str__(self):
        return str(self.pk) + ' | ' + self.name + ' | ' + self.problem.name


class Test(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    index = models.IntegerField()
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    is_example = models.BooleanField(default=False)
    example_answer = models.TextField(blank=True, null=True)
    use_generator = models.BooleanField(default=False)
    generator = models.ForeignKey(Generator, null=True, blank=True,
                                  on_delete=models.SET_NULL)
    data = models.TextField()

    def __str__(self):
        return self.problem.name + ' | ' + str(self.index)


# Submission

class Submission(models.Model):
    CPP17 = 'CPP17'
    PYTHON3 = 'PYTHON3.7'

    SUBMISSION_TYPES = (
        (CPP17, 'gcc C++ 17'),
        (PYTHON3, 'python 3.7'),
    )

    # These are returns code from checker (testlib.h). at line 203
    OK = 'OK'  # code 0
    WA = 'WA'  # code 1
    PE = 'PE'  # code 2

    # POINTS = '7'
    UNEXPECTED_EOF = 'EOF'  # code 8
    UNKNOWN_CODE = 'UC'
    TE = 'TE'
    TLE = 'TLE'
    MLE = 'MLE'
    RE = 'RE'
    CP = 'CP'

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
        (UNKNOWN_CODE, 'Unknown code')
        # (POINTS, 'POINTS'),
    )

    def erase_verdict(self):
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
            return 'In_queue'
        return 'Not in queue'

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    data = models.TextField(blank=True)
    in_queue = models.BooleanField(default=False)
    tested = models.BooleanField(default=False)
    testing = models.BooleanField(default=False)
    testing_message = models.CharField(default='Testing', blank=True,
                                       max_length=128)
    verdict_message = models.CharField(default='', max_length=64)
    verdict_description = models.TextField(default='')
    max_time_used = models.FloatField(default=-1)
    max_memory_used = models.IntegerField(default=-1)
    verdict_debug_message = models.CharField(default='', max_length=64)
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
