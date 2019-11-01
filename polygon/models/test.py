from django.db import models

from polygon.models import Problem
from utils import IndexedModel


class Generator(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=64)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    generator = models.TextField()
    generator_compiled = models.BinaryField(blank=True, null=True)

    def __str__(self):
        return str(self.pk) + ' | ' + self.name + ' | ' + self.problem.name


class TestGroup(IndexedModel):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    points = models.FloatField(default=0)
    name = models.CharField(max_length=64)


class Test(IndexedModel):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    points = models.FloatField(default=0)
    group = models.ForeignKey(TestGroup, on_delete=models.SET_NULL, null=True)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    is_example = models.BooleanField(default=False)
    example_input = models.TextField(blank=True, null=True)
    example_answer = models.TextField(blank=True, null=True)
    use_generator = models.BooleanField(default=False)
    generator = models.ForeignKey(Generator, null=True, blank=True,
                                  on_delete=models.SET_NULL)
    data = models.TextField()

    def __str__(self):
        return self.problem.name + ' | ' + str(self.index)
