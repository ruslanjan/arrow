from django.db import models


# Worker models

class Executor(models.Model):
    host = models.URLField()
    is_ready = models.BooleanField(default=False)
    is_busy = models.BooleanField(default=False)


# Problem related models

class Problem(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=128, unique=True)
    solution = models.TextField(blank=True)
    checker = models.TextField(blank=True)
    is_ready = models.BooleanField(default=False)

    def __str__(self):
        return self.name + ' | ' + str(self.is_ready)


def get_statement_folder(instance, filename):
    return f'problem/{instance.problem.pk}/statement/{instance.pk}/{filename}'


class Statement(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=64, default='Statement')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    pdf_statement = models.FileField(upload_to=get_statement_folder, blank=True)

    # legend = models.TextField(blank=True)
    # input_format = models.TextField(blank=True)
    # output_format = models.TextField(blank=True)
    def __str__(self):
        return self.problem.name + ' | ' + self.name


class Generator(models.Model):
    name = models.CharField(max_length=64)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    generator = models.TextField()

    def __str__(self):
        return self.problem.name + ' | ' + self.name


class Test(models.Model):
    index = models.IntegerField()
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    is_example = models.BooleanField(default=False)
    use_generator = models.BooleanField(default=False)
    generator = models.ForeignKey(Generator, null=True,
                                  on_delete=models.SET_NULL)
    data = models.TextField()

    def __str__(self):
        return self.problem.name + ' | ' + str(self.index)
