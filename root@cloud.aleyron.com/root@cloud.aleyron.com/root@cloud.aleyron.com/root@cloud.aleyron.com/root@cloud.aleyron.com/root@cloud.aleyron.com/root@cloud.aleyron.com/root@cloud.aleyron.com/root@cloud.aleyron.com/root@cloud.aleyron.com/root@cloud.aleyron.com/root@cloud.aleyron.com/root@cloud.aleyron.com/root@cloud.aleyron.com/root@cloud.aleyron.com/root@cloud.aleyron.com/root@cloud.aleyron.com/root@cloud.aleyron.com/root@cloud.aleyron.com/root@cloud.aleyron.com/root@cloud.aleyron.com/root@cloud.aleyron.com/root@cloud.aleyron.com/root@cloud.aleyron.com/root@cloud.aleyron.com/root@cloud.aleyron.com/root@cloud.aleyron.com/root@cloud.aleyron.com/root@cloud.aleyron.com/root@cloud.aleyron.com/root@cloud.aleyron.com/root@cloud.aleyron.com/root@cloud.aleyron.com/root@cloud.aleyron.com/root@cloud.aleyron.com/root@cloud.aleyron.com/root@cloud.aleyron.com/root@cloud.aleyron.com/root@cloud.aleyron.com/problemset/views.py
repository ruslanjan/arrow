from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.http import HttpResponseNotFound
from django.shortcuts import render, redirect, get_object_or_404

from polygon.judge import judge_submission
from .models import *


def check_user_has_problemset_profile_else_create(user: User):
    if not hasattr(user, 'problemsetuserprofile'):
        problemset_user_profile = ProblemsetUserProfile(user=user)
        problemset_user_profile.save()
    return True


@login_required
@user_passes_test(check_user_has_problemset_profile_else_create)
def index(request):
    return view_tasks(request)
    # return render(request, 'problemset/index.html', context={})


@login_required()
@user_passes_test(check_user_has_problemset_profile_else_create)
def submission(request, pk):
    submission = get_object_or_404(Submission, pk=pk)
    return render(request, 'problemset/submission/submission.html',
                  context={
                      'submission': submission,
                      'Submission': Submission,
                  })


@login_required()
@user_passes_test(check_user_has_problemset_profile_else_create)
def submissions(request):
    user_profile = request.user.problemsetuserprofile
    submissions = ProblemsetSubmission.objects.all().order_by('-pk')
    return render(request, 'problemset/submission/submissions.html',
                  context={
                      'submissions': submissions,
                      'Submission': Submission
                  })


@login_required()
@user_passes_test(check_user_has_problemset_profile_else_create)
def my_submissions(request):
    user_profile = request.user.problemsetuserprofile
    submissions = ProblemsetSubmission.objects.filter(user_profile=user_profile).order_by('-pk')
    return render(request, 'problemset/submission/my_submissions.html',
                  context={
                      'submissions': submissions,
                      'Submission': Submission
                  })


@login_required()
@user_passes_test(check_user_has_problemset_profile_else_create)
def view_task(request, pk):
    task = get_object_or_404(ProblemsetTask, pk=pk)
    user_profile = request.user.problemsetuserprofile
    if task.is_active is False or task.problem is None:
        return HttpResponseNotFound(task.name)
    return render(request, 'problemset/task/task.html', context={
        'task': task,
        'profile': user_profile,
        'Submission': Submission
    })


@login_required
@user_passes_test(check_user_has_problemset_profile_else_create)
def view_tasks(request):
    tasks = ProblemsetTask.objects.exclude(problem=None).filter(is_active=True)
    user_profile = request.user.problemsetuserprofile
    return render(request, 'problemset/task/tasks.html', context={
        'tasks': tasks,
        'profile': user_profile,
        'Submission': Submission
    })


class SubmitForm(forms.Form):
    submission_type = forms.ChoiceField(required=True, choices=Submission.SUBMISSION_TYPES)
    data = forms.CharField(required=True)

@login_required
@user_passes_test(check_user_has_problemset_profile_else_create)
def submit_solution(request, pk):
    task = get_object_or_404(ProblemsetTask, pk=pk)
    user_profile = request.user.problemsetuserprofile
    form = SubmitForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            # with transaction.atomic():
            submission = Submission(submission_type=form.cleaned_data['submission_type'],
                                    data=form.cleaned_data['data'],
                                    user=request.user,
                                    problem=task.problem)
            submission.save()
            problemset_submission = ProblemsetSubmission(problemset_task=task,
                                                         submission=submission,
                                                         user_profile=user_profile,)
            problemset_submission.save()
            judge_submission(submission)

    return redirect('problemset.views.my_submissions')


# Task
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
