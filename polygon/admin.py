from django.contrib import admin

# Register your models here.
from polygon.models import Problem, Statement, Test, Executor, Submission

admin.site.register(Problem)
admin.site.register(Statement)
admin.site.register(Test)
admin.site.register(Executor)
admin.site.register(Submission)
