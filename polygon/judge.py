from celery import chord

from polygon.models import Submission
from .tasks import prepare_sandbox_config_for_submission, run_sandbox, \
    parse_sandbox_result, \
    apply_submission_result_for_submission, \
    prepare_sandbox_config_for_submission_on_error


def judge_submission(submission: Submission, start=True):
    submission.tested = False
    submission.save()
    task = chord([(prepare_sandbox_config_for_submission.s(submission.pk,
                                                    test.pk).on_error(
        prepare_sandbox_config_for_submission_on_error.s(submission.pk,
                                                         test.pk)) | run_sandbox.s() | parse_sandbox_result.s(
        submission.pk, test.pk)) for test in submission.problem.test_set.all()],
          apply_submission_result_for_submission.s(submission.pk))
    if start:
        task()
    else:
        return task
