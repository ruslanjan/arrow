import json

from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Max
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render, redirect, HttpResponse

from polygon.models import Problem, TestGroup


class CreateTestGroupForm(forms.ModelForm):
    class Meta:
        model = TestGroup
        fields = ('name',)


@login_required()
@staff_member_required()
def create_test_group(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    form = CreateTestGroupForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            test_group: TestGroup = form.save(commit=False)
            test_group.problem = problem
            next_test_index = TestGroup.objects.filter(
                problem=problem).aggregate(Max('index'))
            test_group.index = next_test_index['index__max'] + 1 if \
                next_test_index['index__max'] is not None else 0
            test_group.save()
            messages.success(request, f'Group "{test_group.name}" created.')
            return redirect('polygon.views.tests', pk=pk)
    return render(request, 'polygon/test_group/create_test_group.html',
                  context={
                      'problem': problem,
                      'form': form,
                  })


@login_required()
@staff_member_required()
@transaction.atomic
def reorder_test_groups(request, pk):
    if request.method == 'POST':
        problem = get_object_or_404(Problem, pk=pk)
        new_order: dict = json.loads(request.body)
        try:
            for test_group_pk, index in new_order.items():
                int(test_group_pk)
                int(index)
        except Exception:
            return HttpResponseBadRequest()
        for test_group_pk, index in new_order.items():
            test_group = get_object_or_404(TestGroup, pk=test_group_pk,
                                           problem=problem)
            test_group.index = index
            test_group.save()
        return HttpResponse('ok')
    return HttpResponseBadRequest()


class EditTestGroupForm(forms.ModelForm):
    save_and_exit = forms.BooleanField(required=False)

    class Meta:
        model = TestGroup
        fields = ('name', 'points')


@login_required()
@staff_member_required()
def view_test_group(request, problem_id, pk):
    problem = get_object_or_404(Problem, pk=problem_id)
    test_group = get_object_or_404(TestGroup, pk=pk, problem=problem)
    form = EditTestGroupForm(request.POST or None, instance=test_group)
    if request.method == 'POST':
        if form.is_valid():
            m = form.save()
            messages.success(request, f'Test Group #{test_group.index} saved')
            if form.cleaned_data['save_and_exit']:
                return redirect('polygon.views.tests', pk=problem_id)

    return render(request, 'polygon/test_group/test_group.html', context={
        'test_group': test_group,
        'problem': problem,
        'form': form,
    })


@login_required()
@staff_member_required()
def delete_test_group(request, problem_id, pk):
    problem = get_object_or_404(Problem, pk=problem_id)
    test_group = get_object_or_404(TestGroup, pk=pk, problem=problem)
    test_group.delete()
    messages.success(request, f'Group "{test_group.name}" deleted.')
    return redirect('polygon.views.tests', pk=problem.pk)
