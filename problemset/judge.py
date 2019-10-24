from polygon.judge import judge_submission
from .models import *
from .tasks import process_submission


def judge_problemset_submission(problemset_submission: ProblemsetSubmission):
    submission = problemset_submission.submission
    task = judge_submission(submission, commit=False)
    (task | process_submission.s(
        problemset_submission.pk)).apply_async()
