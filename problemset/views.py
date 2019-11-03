import re

import django_filters
from captcha.fields import CaptchaField
from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from polygon.judge import judge_submission
from polygon.models import Statement
from problemset.judge import judge_problemset_submission
from .models import *
from .tasks import *


def index(request):
    return view_tasks(request)
    # return render(request, 'problemset/index.html', context={})


def submission(request, pk):
    # user_profile = request.user.problemsetuserprofile
    problemset_submission = get_object_or_404(ProblemsetSubmission, pk=pk)
    show_data = False
    if request.user.is_staff or problemset_submission.user_profile.user == request.user:
        show_data = True

    return render(request, 'problemset/submission/submission.html',
                  context={
                      'problemset_submission': problemset_submission,
                      'submission': problemset_submission.submission,
                      'test_group_results': problemset_submission.submission.submissiontestgroupresult_set.order_by('test_group__index'),
                      'test_results': problemset_submission.submission.submissiontestresult_set.order_by('test__index'),
                      'Submission': Submission,
                      'show_data': show_data
                  })


def submissions(request):
    problemset_submissions = ProblemsetSubmission.objects.all().order_by('-pk')
    paginator = Paginator(problemset_submissions,
                          25)  # Show 25 submissions per page
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

@staff_member_required
def rejudge_submission(request, pk):
    problemset_submission = get_object_or_404(ProblemsetSubmission, pk=pk)
    judge_problemset_submission(problemset_submission)
    return redirect('problemset.views.submission', pk=pk)


# Submissions
# +=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=
# Tasks

class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = ProblemsetTask
        fields = ['name', 'tags']


def view_tasks(request):
    all_tasks = ProblemsetTask.objects.exclude(problem=None).filter(
        is_active=True).order_by('-pk')
    tasks_filter = ProductFilter(request.GET, queryset=all_tasks)
    all_tasks = tasks_filter.qs

    paginator = Paginator(all_tasks,
                          25)  # Show 25 contacts per page
    page = int(request.GET.get('page')) if str(
        request.GET.get('page')).isnumeric() else 1
    if page > paginator.num_pages:
        page = paginator.num_pages
    if page < 1:
        page = 1

    tasks = paginator.get_page(page)

    user = request.user
    user_profile = None
    tasks_solved = None
    tasks_tried = None
    if not user.is_anonymous:
        user_profile = request.user.problemsetuserprofile
        tasks_solved = user_profile.problemsetusertaskprofile_set.filter(
            solved=True, problemset_task__in=tasks).values_list(
            'problemset_task__pk', flat=True)
        tasks_tried = user_profile.problemsetusertaskprofile_set.filter(
            solved=False, tried_count__gt=0,
            problemset_task__in=tasks).values_list('problemset_task__pk',
                                                   flat=True)
    return render(request, 'problemset/task/tasks.html', context={
        'tasks': tasks,
        'Submission': Submission,
        'user_profile': user_profile,
        'tasks_solved': tasks_solved,
        'tasks_tried': tasks_tried,
        'page': page,
        'num_pages': paginator.num_pages,
        'previous_page': page - 1 if page >= 1 else None,
        'next_page': page + 1 if page + 1 <= paginator.num_pages else None,
        'filter': tasks_filter,
        'all_tags': ProblemsetTaskTag.objects.all()
    })


class SubmitForm(forms.Form):
    submission_type = forms.ChoiceField(required=True,
                                        choices=Submission.SUBMISSION_TYPES)
    data = forms.CharField(required=True, max_length=128000)
    # captcha = CaptchaField()


def view_task(request, pk):
    task = get_object_or_404(ProblemsetTask, pk=pk, is_active=True)
    # user_profile = request.user.problemsetuserprofile
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
    form = None
    use_captcha = True
    if not request.user.is_anonymous:
        form = SubmitForm(request.POST or None)

    if request.method == 'POST' and not request.user.is_anonymous:
        maximum_submissions = 6
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
            created_time = timezone.now() - timezone.timedelta(seconds=3)
            user_profile = request.user.problemsetuserprofile
            submissions_count = ProblemsetSubmission.objects.filter(
                user_profile=user_profile,
                created_at__gte=created_time,
                submission__tested=False,
                submission__in_queue=True,
            ).count()
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
                judge_problemset_submission(problemset_submission)
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
        'use_captcha': use_captcha
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
# ==============================================================================
# User Profile

def view_profile(request, username):
    user = get_object_or_404(User, username=username)
    user_profile = get_object_or_404(ProblemsetUserProfile,
                                     user__username=username)
    tasks_solved = user_profile.problemsetusertaskprofile_set.filter(
        solved=True)
    return render(request, 'problemset/user_profile/profile.html', context={
        'user_profile': user_profile,
        'tasks_solved': tasks_solved
    })


# User Profile
# ==============================================================================
#
# +=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=
# Management
# ==============================================================================
# Manage Task Tags

@staff_member_required()
def manage_tags(request):
    tags = ProblemsetTaskTag.objects.all()
    print(tags)
    return render(request, 'problemset/task/tag/manage_tags.html', context={
        'tags': tags
    })


class CreateTagForm(forms.ModelForm):
    class Meta:
        model = ProblemsetTaskTag
        fields = ('name',)


@staff_member_required()
def add_tag(request):
    form = CreateTagForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            if re.match(r'[^\s,]+$', form.cleaned_data['name']):
                tag: ProblemsetTaskTag = form.save()
                messages.success(request, f'Tag "{tag.name}" added!')
                return redirect('problemset.views.manage_tags')
            else:
                messages.error(request, 'No whitespace and comma!')

    return render(request, 'problemset/task/tag/add_tag.html', {
        'form': form
    })


@staff_member_required()
def delete_tag(request, pk):
    tag = get_object_or_404(ProblemsetTaskTag, pk=pk)
    if request.method == 'POST':
        tag.delete()
        messages.success(request, f'Tag "{tag.name}" deleted!')
        return redirect('problemset.views.manage_tags')
    return render(request, 'problemset/task/tag/delete_tag.html', context={
        'tag': tag
    })


# Manage Task Tags
# ==============================================================================
# Manage Tasks


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
        'problems': Problem.objects.filter(is_active=True).order_by('-pk')
    })


class TaskTagsForm(forms.Form):
    save_and_exit = forms.BooleanField(required=False)
    tags = forms.CharField()


@staff_member_required
@transaction.atomic
def manage_task_tags(request, pk):
    task = get_object_or_404(ProblemsetTask, pk=pk)
    tags = ', '.join(task.tags.all().values_list('name', flat=True))
    form = TaskTagsForm(request.POST or None, initial={'tags': tags})

    if request.method == 'POST':
        if form.is_valid():
            new_tags = form.cleaned_data['tags']
            new_tags = new_tags.split(', ')
            for tag in new_tags:
                if not re.match(r'[^\s,]+$', tag):
                    messages.error(request, 'Wrong format')
                    return render(request,
                                  'problemset/task/manage_task_tags.html',
                                  context={
                                      'form': form, 'task': task, 'tags': tags
                                  })
            for tag in new_tags:
                if not ProblemsetTaskTag.objects.filter(name=tag).exists():
                    messages.error(request, f'Tag "{tag}" does not exist.')
                    return render(request,
                                  'problemset/task/manage_task_tags.html',
                                  context={
                                      'form': form, 'task': task, 'tags': tags
                                  })
            task.tags.clear()
            for tag in new_tags:
                task.tags.add(ProblemsetTaskTag.objects.get(name=tag))
            task.save()
            messages.success(request, f'Tags for task "{task.name}" saved')
            if form.cleaned_data['save_and_exit']:
                return redirect('problemset.views.manage_tasks')

    return render(request, 'problemset/task/manage_task_tags.html', context={
        'form': form, 'task': task, 'tags': tags,
        'all_tags': ProblemsetTaskTag.objects.all().values_list('name', flat=True)
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
