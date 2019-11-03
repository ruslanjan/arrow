from django.db.models import Sum

from arrow.celery import app
from .models import *


@app.task()
def update_contest_status():
    print('Contest update')
    contests = Contest.objects.filter(is_launched=True, is_ended=False)
    for contest in contests:
        if not contest.is_started and timezone.now() >= contest.start_date_time:
            contest.is_started = True
            contest.save()
        elif timezone.now() >= contest.start_date_time + timezone.timedelta(
                seconds=contest.duration):
            contest.is_ended = True
            contest.save()


bad_verdicts = {
    Submission.WA,
    Submission.RE,
    Submission.TLE,
    Submission.MLE,
    Submission.PE
}


@app.task()
def process_submission(_, contest_submission_id: ContestUserSubmission):
    contest_submission = ContestUserSubmission.objects.get(
        pk=contest_submission_id)
    contest = contest_submission.contest
    contest_user_task_profile = contest_submission.user_task_profile
    is_upsolving = contest_submission.upsolving
    user_profile = contest_submission.user_profile
    if contest.is_started:
        if not contest.is_ioi_style:
            if not is_upsolving:
                if not contest_user_task_profile.solved:
                    if contest_submission.submission.verdict == Submission.OK:
                        contest_user_task_profile.solved = True
                        # add penalty to user
                        penalty = (
                                          contest_submission.created_at - contest.start_date_time).seconds / 60
                        contest_user_task_profile.penalty += penalty
                    elif contest_submission.submission.verdict in bad_verdicts:
                        contest_user_task_profile.tries += 1
                        contest_user_task_profile.penalty += 20
            else:
                if not contest_user_task_profile.solved_after_contest:
                    if contest_submission.submission.verdict == Submission.OK:
                        contest_user_task_profile.solved_after_contest = True
                    elif contest_submission.submission.verdict in bad_verdicts:
                        contest_user_task_profile.tries_after_contest += 1
        else:
            if not is_upsolving:
                contest_user_task_profile.points = max(
                    contest_user_task_profile.points,
                    contest_submission.submission.points)
                contest_user_task_profile.tries += 1
            else:
                contest_user_task_profile.points_after_contest = max(
                    contest_user_task_profile.points_after_contest,
                    contest_submission.submission.points)
                contest_user_task_profile.tries += 1
    contest_user_task_profile.save()
    if contest.is_started:
        if not contest.is_ioi_style:
            if not is_upsolving:
                # update user profile
                user_profile.solved_count = user_profile.contestusertaskprofile_set.filter(
                    solved=True).count()
                user_profile.penalty = \
                    user_profile.contestusertaskprofile_set.aggregate(
                        Sum('penalty'), )['penalty__sum']
            else:
                # update user profile
                user_profile.solved_count_after_contest = \
                    user_profile.contestusertaskprofile_set.filter(
                        solved_after_contest=True).count()
        else:
            if not is_upsolving:
                user_profile.points += \
                    user_profile.contestusertaskprofile_set.aggregate(
                        Sum('points'))['points__sum']
            else:
                user_profile.points_after_contest += \
                    user_profile.contestusertaskprofile_set.aggregate(
                        Sum('points_after_contest'))['points_after_contest__sum']
    user_profile.save()
