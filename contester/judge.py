from polygon.judge import judge_submission
from .models import *
from .tasks import process_submission


def judge_contest_submission(problemset_submission: ContestUserSubmission):
    submission = problemset_submission.submission
    task = judge_submission(submission, commit=False)
    (task | process_submission.s(
        problemset_submission.pk)).apply_async()
