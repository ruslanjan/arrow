from celery import chord

from polygon.models import Submission
from .tasks import judge_submission_task, \
    sandbox_run_on_error


def judge_submission(submission: Submission, commit=True):
    submission.erase_verdict()
    submission.in_queue = True
    submission.save()
    task = judge_submission_task.s(submission.pk).on_error(sandbox_run_on_error.s(submission.pk))
    if commit:
        task.apply_async()
    else:
        return task
