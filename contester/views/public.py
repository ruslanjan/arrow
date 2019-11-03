from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404, redirect

from contester.judge import judge_contest_submission
from contester.models import *
from polygon.models import Statement


# Checks and utils
def check_contest_started(func):
    def wrapper_check_contest_started(request, contest_id, *args, **kwargs):
        contest = get_object_or_404(Contest, pk=contest_id)
        if contest.is_started and contest.is_launched:
            return func(request, *args, contest_id=contest_id, **kwargs)
        else:
            return HttpResponseBadRequest('contest is not started or not '
                                          'available')

    return wrapper_check_contest_started


def index(request):
    contests = Contest.objects.filter(is_public=True, is_launched=True).filter(
        Q(start_date_time__gte=timezone.now()) |
        Q(is_ended=False, is_started=True))
    past_contests = Contest.objects.filter(is_public=True,
                                           is_ended=True,
                                           is_launched=True)
    return render(request, 'contester/index.html', {
        'current_contests': contests,
        'past_contests': past_contests,
        'registered_contests': Contest.objects.filter(
            contestuserprofile__user=request.user) if not request.user.is_anonymous else []
    })

@login_required
def my_contests(request):
    contests = Contest.objects.filter(is_launched=True,
                                      contestuserprofile__user=request.user).filter(
        Q(start_date_time__gte=timezone.now()) |
        Q(is_ended=False, is_started=True))
    past_contests = Contest.objects.filter(contestuserprofile__user=request.user,
                                           is_ended=True,
                                           is_launched=True)
    return render(request, 'contester/my_contests.html', {
        'current_contests': contests,
        'past_contests': past_contests,
        'registered_contests': Contest.objects.filter(
            contestuserprofile__user=request.user)
    })


@login_required
def register_to_contest(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    if contest.is_public and contest.is_launched and not request.user.contestuserprofile_set.filter(
            contest=contest).exists():
        user_profile = ContestUserProfile(contest=contest,
                                          user=request.user)
        user_profile.save()
        messages.success(request, f'You registered to "{contest.name}"')
    else:
        messages.error(
            request,
            f'You already registered to "{contest.name}" or bad request')
    return redirect('contester.views.index')


@check_contest_started
def view_contest_tasks(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    return render(request, 'contester/contest/tasks.html', context={
        'contest': contest,
        'tasks': contest.contesttask_set.order_by('index')
    })


@login_required
@check_contest_started
def view_user_profile_summary(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    if not request.user.contestuserprofile_set.filter(
            contest=contest).exists():
        return HttpResponseForbidden('You are not registered to contest')
    user_profile = request.user.contestuserprofile_set.get(contest=contest)
    return render(request, 'contester/contest/user_profile_summary.html',
                  context={
                      'contest': contest,
                      'user_profile': user_profile,
                      'task_profiles': user_profile.contestusertaskprofile_set.order_by(
                          'task__index')
                  })


@login_required
@check_contest_started
def submission(request, contest_id, pk):
    contest = get_object_or_404(Contest, pk=contest_id)
    contest_submission = get_object_or_404(ContestUserSubmission, pk=pk,
                                           contest=contest)
    show_data = True if request.user.is_staff or contest_submission.user_profile.user == request.user else False
    return render(request, 'contester/contest/submission.html', context={
        'contest': contest,
        'contest_submission': contest_submission,
        'test_group_results': contest_submission.submission.submissiontestgroupresult_set.order_by(
            'test_group__index'),
        'test_results': contest_submission.submission.submissiontestresult_set.order_by(
            'test__index'),
        'Submission': Submission,
        'show_data': show_data
    })


@login_required
@check_contest_started
def my_submissions(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    if not request.user.contestuserprofile_set.filter(
            contest=contest).exists():
        return HttpResponseForbidden('You are not registered to contest')
    user_profile = request.user.contestuserprofile_set.get(contest=contest)
    return render(request, 'contester/contest/my_submissions.html', context={
        'contest': contest,
        'contest_submissions': user_profile.contestusersubmission_set.order_by('-pk'),
        'Submission': Submission
    })


@check_contest_started
def contest_submissions(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    contest_submissions = ContestUserSubmission.objects.filter(
        contest=contest).order_by('-pk')
    paginator = Paginator(contest_submissions,
                          25)  # Show 25 submissions per page
    page = int(request.GET.get('page')) if str(
        request.GET.get('page')).isnumeric() else 1

    return render(request, 'contester/contest/submissions.html',
                  context={
                      'contest': contest,
                      'contest_submissions': paginator.get_page(page),
                      'Submission': Submission,
                      'previous_page': page - 1 if page >= 1 else None,
                      'next_page': page + 1 if page + 1 <= paginator.num_pages else None
                  })


@check_contest_started
def contest_standings(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)

    upsolving_user_profiles = None
    if not contest.is_ioi_style:
        user_profiles = contest.contestuserprofile_set.order_by('-solved_count',
                                                                'penalty').exclude(solved_count=0)
        if contest.is_ended:
            upsolving_user_profiles = contest.contestuserprofile_set.order_by(
                '-solved_count_after_contest').exclude(solved_count_after_contest=0)
    else:
        user_profiles = contest.contestuserprofile_set.order_by('points').exclude(points=0)
        if contest.is_ended:
            upsolving_user_profiles = contest.contestuserprofile_set.order_by(
                '-points_after_contest').exclude(points_after_contest=0)

    return render(request, 'contester/contest/standings.html', context={
        'contest': contest,
        'user_profiles': user_profiles,
        'upsolving_user_profiles': upsolving_user_profiles,
    })


class SubmitForm(forms.Form):
    submission_type = forms.ChoiceField(required=True,
                                        choices=Submission.SUBMISSION_TYPES)
    data = forms.CharField(required=True, max_length=128000)
    # captcha = CaptchaField()


@login_required
@check_contest_started
def view_contest_task(request, contest_id, pk):
    contest = get_object_or_404(Contest, pk=contest_id)
    task = get_object_or_404(ContestTask, pk=pk, contest=contest)

    statement = None
    if task.problem.statement_set.filter(is_default=True,
                                         is_visible=True).exists():
        statement = task.problem.statement_set.get(is_default=True,
                                                   is_visible=True)
    if request.GET.get('statement') and str(
            request.GET.get('statement')).isnumeric():
        statement = get_object_or_404(Statement,
                                      pk=int(request.GET.get('statement')),
                                      is_visible=True)
    statements = task.problem.statement_set.filter(is_visible=True)
    if statement:
        statements = statements.exclude(pk=statement.pk)
    form = SubmitForm(request.POST or None)
    use_captcha = True

    if request.method == 'POST' and not request.user.is_anonymous:
        if not request.user.contestuserprofile_set.filter(
                contest=contest).exists():
            return HttpResponseForbidden('You are not registered to contest')
        user_profile = request.user.contestuserprofile_set.get(contest=contest)
        # check if user spamming
        maximum_submissions = 12
        minutes_limit = 1
        created_time = timezone.now() - timezone.timedelta(
            minutes=minutes_limit)
        submissions_count = ContestUserSubmission.objects.filter(
            user_profile=user_profile,
            created_at__gte=created_time,
            submission__tested=False,
            submission__in_queue=True,
        ).count()
        if submissions_count < maximum_submissions:
            created_time = timezone.now() - timezone.timedelta(seconds=1)
            submissions_count = ContestUserSubmission.objects.filter(
                user_profile=user_profile,
                created_at__gte=created_time,
                submission__tested=False,
                submission__in_queue=True,
            ).count()
            # if users accidentally sends twice
            if submissions_count > 0:
                messages.error(request,
                               f'Please, do\'t spam :).')
            elif form.is_valid():
                # with transaction.atomic():
                submission = Submission(
                    submission_type=form.cleaned_data['submission_type'],
                    data=form.cleaned_data['data'],
                    user=request.user,
                    problem=task.problem)
                submission.save()

                if user_profile.contestusertaskprofile_set.filter(
                        task=task, contest=contest).exists():
                    contest_user_task_profile = user_profile.contestusertaskprofile_set.get(
                        task=task, contest=contest)
                else:
                    contest_user_task_profile = ContestUserTaskProfile(
                        task=task,
                        contest=contest,
                        user_profile=user_profile)
                    contest_user_task_profile.save()

                contest_submission = ContestUserSubmission(
                    task=task,
                    contest=contest,
                    submission=submission,
                    upsolving=contest.get_end_datetime() < timezone.now(),
                    user_profile=user_profile,
                    user_task_profile=contest_user_task_profile
                )
                contest_submission.save()
                judge_contest_submission(contest_submission)
                return redirect('contester.views.my_submissions',
                                contest_id=contest.pk)
            else:
                messages.error(request,
                               f'Invalid submit form!')
        else:
            messages.error(request,
                           f'No more then {maximum_submissions} submissions in {minutes_limit} minute{"s" if minutes_limit > 1 else ""}!')
    return render(request, 'contester/contest/task.html', context={
        'task': task,
        'contest': contest,
        'Submission': Submission,
        'statement': statement,
        'statements': statements,
        'form': form,
        'use_captcha': use_captcha
    })
