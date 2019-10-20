from captcha.fields import CaptchaField
from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from polygon.judge import judge_submission
from polygon.models import Statement
from .models import *
from .tasks import *


def index(request):
    return view_tasks(request)
    # return render(request, 'problemset/index.html', context={})


@login_required
def submission(request, pk):
    # user_profile = request.user.problemsetuserprofile
    problemset_submission = get_object_or_404(ProblemsetSubmission, pk=pk)
    return render(request, 'problemset/submission/submission.html',
                  context={
                      'problemset_submission': problemset_submission,
                      'submission': problemset_submission.submission,
                      'Submission': Submission,
                  })


def submissions(request):
    problemset_submissions = ProblemsetSubmission.objects.all().order_by('-pk')
    paginator = Paginator(problemset_submissions,
                          25)  # Show 25 contacts per page
    page = int(request.GET.get('page')) if str(
        request.GET.get('page')).isnumeric() else 1

    return render(request, 'problemset/submission/submissions.html',
                  context={
                      'problemset_submissions': paginator.get_page(page),
                      'Submission': Submission,
                      'previous_page': page - 1 if page >= 1 else None,
                      'next_page': page + 1 if page + 1 <= paginator.num_pages else None
                  })


@login_required()
def my_submissions(request):
    user_profile = request.user.problemsetuserprofile
    problemset_submissions = ProblemsetSubmission.objects.filter(
        user_profile=user_profile).order_by('-pk')
    paginator = Paginator(problemset_submissions,
                          25)  # Show 25 contacts per page
    page = int(request.GET.get('page')) if str(
        request.GET.get('page')).isnumeric() else 1
    return render(request, 'problemset/submission/my_submissions.html',
                  context={
                      'problemset_submissions': paginator.get_page(page),
                      'Submission': Submission,
                      'previous_page': page - 1 if page >= 1 else None,
                      'next_page': page + 1 if page + 1 <= paginator.num_pages else None
                  })


def view_tasks(request):
    user = request.user
    user_profile = None
    tasks_solved = None
    tasks_tried = None
    if not user.is_anonymous:
        user_profile = request.user.problemsetuserprofile
        tasks_solved = user_profile.problemsetusertaskprofile_set.filter(
            solved=True).values_list('problemset_task__pk', flat=True)
        tasks_tried = user_profile.problemsetusertaskprofile_set.filter(
            solved=False, tried_count__gt=0).values_list('problemset_task__pk',
                                                         flat=True)
    tasks = ProblemsetTask.objects.exclude(problem=None).filter(is_active=True)
    return render(request, 'problemset/task/tasks.html', context={
        'tasks': tasks,
        'Submission': Submission,
        'user_profile': user_profile,
        'tasks_solved': tasks_solved,
        'tasks_tried': tasks_tried
    })


class SubmitForm(forms.Form):
    submission_type = forms.ChoiceField(required=True,
                                        choices=Submission.SUBMISSION_TYPES)
    data = forms.CharField(required=True, max_length=128000)
    captcha = CaptchaField()


def view_task(request, pk):
    task = get_object_or_404(ProblemsetTask, pk=pk, is_active=True)
    # user_profile = request.user.problemsetuserprofile
    statement = None
    if task.problem.statement_set.filter(is_default=True, is_visible=True).exists():
        statement = task.problem.statement_set.get(is_default=True, is_visible=True)
    if request.GET.get('statement') and str(
            request.GET.get('statement')).isnumeric():
        statement = get_object_or_404(Statement,
                                      pk=int(request.GET.get('statement')),
                                      is_visible=True)
    statements = task.problem.statement_set.filter(is_visible=True)
    if statement:
        statements = statements.exclude(pk=statement.pk)
    form = None
    if not request.user.is_anonymous:
        form = SubmitForm(request.POST or None)

    if request.method == 'POST' and not request.user.is_anonymous:
        maximum_submissions = 3
        minutes_limit = 1
        created_time = timezone.now() - timezone.timedelta(
            minutes=minutes_limit)
        user_profile = request.user.problemsetuserprofile
        submissions_count = ProblemsetSubmission.objects.filter(
            user_profile=user_profile,
            created_at__gte=created_time,
            submission__tested=False,
            submission__in_queue=True,
        ).count()
        if submissions_count < maximum_submissions:
            if form.is_valid():
                # with transaction.atomic():
                submission = Submission(
                    submission_type=form.cleaned_data['submission_type'],
                    data=form.cleaned_data['data'],
                    user=request.user,
                    problem=task.problem)
                submission.save()
                problemset_user_task_profile = None
                if user_profile.problemsetusertaskprofile_set.filter(
                        problemset_task=task).exists():
                    problemset_user_task_profile = user_profile.problemsetusertaskprofile_set.get(
                        problemset_task=task)
                else:
                    problemset_user_task_profile = ProblemsetUserTaskProfile(
                        problemset_task=task,
                        user_profile=user_profile, )
                    problemset_user_task_profile.save()

                problemset_submission = ProblemsetSubmission(
                    problemset_task=task,
                    submission=submission,
                    user_profile=user_profile,
                    user_task_profile=problemset_user_task_profile
                )
                problemset_submission.save()
                task = judge_submission(submission, commit=False)
                (task | process_submission.s(
                    problemset_submission.pk)).apply_async()
                return redirect('problemset.views.my_submissions')
            else:
                messages.error(request,
                               f'Invalid submit form!')
        else:
            messages.error(request,
                           f'No more then {maximum_submissions} submission in {minutes_limit} minute{"s" if minutes_limit > 1 else ""}!')

    return render(request, 'problemset/task/task.html', context={
        'task': task,
        'Submission': Submission,
        'statement': statement,
        'statements': statements,
        'form': form,
    })


# @login_required
# def submit_solution(request, pk):
#     maximum_submissions = 3
#     minutes_limit = 1
#     created_time = timezone.now() - timezone.timedelta(minutes=minutes_limit)
#     task = get_object_or_404(ProblemsetTask, pk=pk, is_active=True)
#     user_profile = request.user.problemsetuserprofile
#     submissions_count = ProblemsetSubmission.objects.filter(
#         user_profile=user_profile,
#         created_at__gte=created_time,
#         submission__tested=False,
#         submission__in_queue=True,
#     ).count()
#     form = SubmitForm(request.POST or None)
#     if request.method == 'POST':
#         if submissions_count < maximum_submissions:
#             if form.is_valid():
#                 # with transaction.atomic():
#                 submission = Submission(
#                     submission_type=form.cleaned_data['submission_type'],
#                     data=form.cleaned_data['data'],
#                     user=request.user,
#                     problem=task.problem)
#                 submission.save()
#                 problemset_user_task_profile = None
#                 if user_profile.problemsetusertaskprofile_set.filter(
#                         problemset_task=task).exists():
#                     problemset_user_task_profile = user_profile.problemsetusertaskprofile_set.get(
#                         problemset_task=task)
#                 else:
#                     problemset_user_task_profile = ProblemsetUserTaskProfile(
#                         problemset_task=task,
#                         user_profile=user_profile, )
#                     problemset_user_task_profile.save()
#
#                 problemset_submission = ProblemsetSubmission(
#                     problemset_task=task,
#                     submission=submission,
#                     user_profile=user_profile,
#                     user_task_profile=problemset_user_task_profile
#                 )
#                 problemset_submission.save()
#                 task = judge_submission(submission, commit=False)
#                 (task | process_submission.s(
#                     problemset_submission.pk)).apply_async()
#             else:
#                 messages.error(request,
#                                f'Invalid submit form!')
#                 return redirect('problemset.views.task', pk=task.pk)
#         else:
#             messages.error(request,
#                            f'No more then {maximum_submissions} submission in {minutes_limit} minute{"s" if minutes_limit > 1 else ""}!')
#             return redirect('problemset.views.task', pk=task.pk)
#
#     return redirect('problemset.views.my_submissions')


# Task
# Task
# ==============================================================================
# User Profile

def view_profile(request, username):
    user = get_object_or_404(User, username=username)
    user_profile = get_object_or_404(ProblemsetUserProfile,
                                     user__username=username)
    tasks_solved = user_profile.problemsetusertaskprofile_set.filter(
        solved=True)
    return render(request, 'problemset/user_profile/profile.html', context={
        'user': user,
        'user_profile': user_profile,
        'tasks_solved': tasks_solved
    })


# User Profile
# ==============================================================================
# Management


class CreateTaskForm(forms.ModelForm):
    class Meta:
        model = ProblemsetTask
        fields = ('name',)


@staff_member_required
def add_task(request):
    form = CreateTaskForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            task = form.save(commit=False)
            task.save()
            return redirect('problemset.views.manage_task', pk=task.pk)
    return render(request, 'problemset/task/add_task.html', context={
        'form': form,
    })


@staff_member_required
def manage_tasks(request):
    tasks = ProblemsetTask.objects.all().order_by('-pk')
    return render(request, 'problemset/task/manage_tasks.html', context={
        'tasks': tasks
    })


class TaskForm(forms.ModelForm):
    save_and_exit = forms.BooleanField(required=False)

    class Meta:
        model = ProblemsetTask
        fields = ('name', 'problem', 'is_active')


@staff_member_required
def manage_task(request, pk):
    task = get_object_or_404(ProblemsetTask, pk=pk)
    form = TaskForm(request.POST or None, instance=task)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f'Task "{task.name}" saved')
            if form.cleaned_data['save_and_exit']:
                return redirect('problemset.views.manage_tasks')

    return render(request, 'problemset/task/manage_task.html', context={
        'form': form, 'task': task,
        'problems': Problem.objects.all().order_by('-pk')
    })


class DeleteTaskForm(forms.Form):
    name = forms.CharField(max_length=128, required=True)


@staff_member_required
def delete_task(request, pk):
    task = get_object_or_404(ProblemsetTask, pk=pk)
    form = DeleteTaskForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            if form.cleaned_data['name'] == task.name:
                task.delete()
                messages.success(request, f"Task {task.name} deleted.")
                return redirect('problemset.views.manage_tasks')
            else:
                messages.error(request, 'names don\'t match')

    return render(request, 'problemset/task/delete_task.html',
                  context={'form': form, 'task': task})
