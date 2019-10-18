from django.contrib import admin

from .models import *

admin.site.register(ProblemsetTask)
admin.site.register(ProblemsetSubmission)
admin.site.register(ProblemsetUserProfile)
admin.site.register(ProblemsetUserTaskProfile)
