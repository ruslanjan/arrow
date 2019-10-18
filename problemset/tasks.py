from arrow.celery import app
from polygon.models import Submission
from problemset.models import ProblemsetSubmission

bad_verdicts = {
    Submission.WA,
    Submission.RE,
    Submission.TLE,
    Submission.MLE,
}


@app.task()
def process_submission(_, problemset_submission_id: ProblemsetSubmission):
    problemset_submission = ProblemsetSubmission.objects.get(
        pk=problemset_submission_id)
    problemset_user_task_profile = problemset_submission.user_task_profile
    if not problemset_user_task_profile.solved:
        if problemset_submission.submission.verdict == Submission.OK:
            problemset_user_task_profile.solved = True
        else:
            problemset_user_task_profile.tried_count += 1
        # elif problemset_submission.submission.verdict in bad_verdicts:
    problemset_user_task_profile.save()
