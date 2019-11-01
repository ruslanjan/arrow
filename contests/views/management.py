import json

from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Max, Q
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404

from contests.models import Contest, ContestTask
from polygon.models import Problem
from utils import reorder_models_indexes


@staff_member_required()
@login_required()
def manage_contests(request):
    return render(request, 'contests/contest/manage/manage_contests.html',
                  context={
                      'contests': Contest.objects.all().order_by('-pk')
                  })


class CreateContestForm(forms.ModelForm):
    class Meta:
        model = Contest
        fields = ('name',)


@staff_member_required()
@login_required()
def create_contest(request):
    form = CreateContestForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            contest = form.save()
            messages.success(request, f'Contest "{contest.name}" created')
            return redirect('contests.views.manage_contest', pk=contest.pk)
    return render(request, 'contests/contest/manage/create_contest.html',
                  context={
                      'form': form
                  })


class ManageContestForm(forms.ModelForm):
    save_and_exit = forms.BooleanField(required=False)
    start_date_time = forms.DateTimeField(input_formats=["%d/%m/%Y %H:%M"])

    class Meta:
        model = Contest
        fields = ('name', 'is_ioi_style', 'start_date_time', 'is_public',
                  'duration')


@staff_member_required()
@login_required()
def manage_contest(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    form = ManageContestForm(request.POST or None, instance=contest)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f'Contest "{contest.name}" saved')
    return render(request, 'contests/contest/manage/manage_contest.html',
                  context={
                      'form': form,
                      'contest': contest,
                  })


class DeleteContestForm(forms.Form):
    name = forms.CharField(max_length=128, required=True)


@staff_member_required()
@login_required()
def delete_contest(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    form = DeleteContestForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            if form.cleaned_data['name'] == contest.name:
                contest.delete()
                messages.success(request,
                                 f"Contest {contest.name} deleted.")
                return redirect('contests.views.manage_contests')
            else:
                messages.error(request, 'names don\'t match')

    return render(request,
                  'contests/contest/manage/delete_contest.html',
                  context={'form': form, 'contest': contest})


# Manage contest tasks

@staff_member_required()
@login_required()
def manage_contest_tasks(request, pk):
    contest: Contest = get_object_or_404(Contest, pk=pk)
    tasks = contest.contesttask_set.order_by('index')
    return render(request,
                  'contests/contest/manage/task/manage_contest_tasks.html',
                  context={
                      'contest': contest,
                      'tasks': tasks
                  })


@staff_member_required()
@login_required()
@transaction.atomic
def reorder_tasks(request, pk):
    if request.method == 'POST':
        contest = get_object_or_404(Contest, pk=pk)
        new_order: dict = json.loads(request.body)
        reorder_models_indexes(contest.contesttask_set.all(), new_order)
        return HttpResponse('ok')
    return HttpResponseBadRequest()


class AddContestTaskForm(forms.ModelForm):
    class Meta:
        model = ContestTask
        fields = ('name',)


@staff_member_required()
@login_required()
def add_contest_task(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    form = AddContestTaskForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            task: ContestTask = form.save(commit=False)
            task.contest = contest
            next_test_index = ContestTask.objects.filter(
                contest=contest).aggregate(Max('index'))
            task.index = next_test_index['index__max'] + 1 if next_test_index[
                                                                  'index__max'] is not None else 0
            task.save()
            messages.success(request, f'Task "{task.name}" created')
            return redirect('contests.views.manage_contest_task',
                            contest_id=contest.pk, pk=task.pk)
    return render(request,
                  'contests/contest/manage/task/add_contest_task.html',
                  context={
                      'contest': contest,
                      'form': form
                  })


class ContestTaskForm(forms.ModelForm):
    save_and_exit = forms.BooleanField(required=False)

    class Meta:
        model = ContestTask
        fields = ('name', 'problem')


@staff_member_required()
@login_required()
def manage_contest_task(request, contest_id, pk):
    contest = get_object_or_404(Contest, pk=contest_id)
    contest_task = get_object_or_404(ContestTask, pk=pk, contest=contest)
    form = ContestTaskForm(request.POST or None, instance=contest_task)
    if request.method == 'POST':
        if form.is_valid():
            contest_task: ContestTask = form.save()
            messages.success(request, f'Task "{contest_task.name}" saved')
            if form.cleaned_data['save_and_exit']:
                return redirect('contests.views.manage_contest_task',
                                problem_id=contest.pk, pk=contest_task.pk)
    problems = Problem.objects.filter(is_active=True)
    if contest.is_ioi_style:
        problems = problems.filter(Q(is_graded=True) |
                                   Q(is_sub_task=True))
    else:
        problems = problems.filter(is_graded=False, is_sub_task=False)
    return render(request,
                  'contests/contest/manage/task/manage_contest_task.html',
                  context={
                      'form': form,
                      'contest': contest,
                      'task': contest_task,
                      'problems': problems
                  })


class DeleteContestTaskForm(forms.Form):
    name = forms.CharField(max_length=128, required=True)


@staff_member_required()
@login_required()
def delete_contest_task(request, contest_id, pk):
    contest = get_object_or_404(Contest, pk=contest_id)
    contest_task = get_object_or_404(ContestTask, pk=pk, contest=contest)
    form = DeleteContestTaskForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            if form.cleaned_data['name'] == contest_task.name:
                contest_task.delete()
                messages.success(request,
                                 f"Task {contest_task.name} from contest {contest.name} deleted.")
                return redirect('contests.views.manage_contest_tasks',
                                pk=contest.pk)
            else:
                messages.error(request, 'names don\'t match')

    return render(request,
                  'contests/contest/manage/task/delete_contest_task.html',
                  context={'form': form, 'task': contest_task,
                           'contest': contest})
