import os
import secrets

from django.contrib.auth.models import User
from django.db import models

from django.db.models.signals import post_delete
from django.dispatch import receiver


class Problem(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=128, unique=True)
    time_limit = models.FloatField(default=1)
    memory_limit = models.IntegerField(default=256000)
    is_interactive = models.BooleanField(default=False)
    is_graded = models.BooleanField(default=False)
    is_sub_task = models.BooleanField(default=False)
    solution = models.TextField(blank=True)
    solution_compiled = models.BinaryField(blank=True, null=True)
    checker = models.TextField(blank=True)
    checker_compiled = models.BinaryField(blank=True, null=True)
    interactor = models.TextField(blank=True, default='')
    interactor_compiled = models.BinaryField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    test_generator_script = models.TextField(blank=True, default="")

    def get_example_tests(self):
        return self.test_set.filter(is_example=True)

    def __str__(self):
        return str(self.pk) + ' | ' + self.name + ' | ' + str(self.is_active)

    class Meta:
        pass


def get_statement_folder(instance, filename):
    return f'problem/{instance.problem.pk}/statement/{instance.pk}/{filename}'


def get_problem_file_folder(instance, filename):
    secrets.token_hex(4)
    filename = f'{filename[:filename.rfind(".")]}_{secrets.token_hex(4)}{filename[filename.rfind("."):]}'
    return f'problem/{instance.problem.pk}/files/{filename}'


class ProblemFile(models.Model):
    problem = models.ForeignKey(
        Problem, blank=True, null=False, on_delete=models.CASCADE)
    file = models.FileField(upload_to=get_problem_file_folder)

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
    interaction = models.TextField(blank=True, default='')
    scoring = models.TextField(blank=True, default='')
    notes = models.TextField(blank=True, default='')
    tutorial = models.TextField(blank=True, default='')

    # legend = models.TextField(blank=True)
    # input_format = models.TextField(blank=True)
    # output_format = models.TextField(blank=True)
    def __str__(self):
        return self.problem.name + ' | ' + self.name

