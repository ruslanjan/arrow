import json
import re

from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Max
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render, HttpResponse

from polygon.models import Problem, Generator, Test, TestGroup


@login_required()
@staff_member_required()
def view_tests(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    return render(request, 'polygon/test/tests.html',
                  context={'problem': problem,
                           'tests': problem.test_set.all().order_by('index'),
                           'test_groups': problem.testgroup_set.all().order_by(
                               'index')
                           })


class CreateTestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ('index', 'data', 'use_generator', 'generator', 'is_example',
                  'example_answer', 'example_input')


@login_required()
@staff_member_required()
def create_test(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    next_test_index = Test.objects.filter(problem=problem).aggregate(
        Max('index'))

    form = CreateTestForm(request.POST or None, initial={
        'index': next_test_index['index__max'] + 1 if next_test_index[
                                                          'index__max'] is not None else '0'})
    if request.method == 'POST':
        if form.is_valid():
            test = form.save(commit=False)
            test.problem = problem
            test.save()
            messages.success(request, f'Test index #{test.index} created')
            return redirect('polygon.views.tests', pk=problem.pk)

    return render(request, 'polygon/test/create_test.html',
                  context={'form': form,
                           'generators': Generator.objects.filter(
                               problem=problem),
                           'problem': problem})


@login_required()
@staff_member_required()
def delete_test(request, problem_id, pk):
    problem = get_object_or_404(Problem, pk=problem_id)
    test = get_object_or_404(Test, pk=pk, problem=problem)
    if test.problem.pk != problem_id:
        messages.error(request, f"test do not belongs to given problem.")
        return redirect('polygon.views.index')
    test.delete()
    messages.success(request,
                     f"test {test.index} from problem {problem.name} deleted.")
    return redirect('polygon.views.tests', pk=problem_id)


class TestForm(forms.ModelForm):
    save_and_exit = forms.BooleanField(required=False)

    class Meta:
        model = Test
        fields = ('index', 'data', 'use_generator', 'generator', 'is_example',
                  'example_answer', 'example_input')


@login_required()
@staff_member_required()
def view_test(request, problem_id, pk):
    test = get_object_or_404(Test, pk=pk)
    form = TestForm(request.POST or None, instance=test)
    problem = get_object_or_404(Problem, pk=problem_id)
    if test.problem.pk != problem_id:
        messages.error(request, f"test do not belongs to given problem.")
        return redirect('polygon.views.index')
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f'Test #{test.index} saved')
            if form.cleaned_data['save_and_exit']:
                return redirect('polygon.views.tests', pk=problem_id)

    return render(request, 'polygon/test/test.html',
                  context={'form': form, 'test': test,
                           'generators': Generator.objects.filter(
                               problem=problem),
                           'problem': problem})


@login_required()
@staff_member_required()
@transaction.atomic
def reindex_tests(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    tests = problem.test_set.all().order_by('index')
    for i in range(len(tests)):
        test = tests[i]
        test.index = i
        test.save()
    return redirect('polygon.views.tests', pk=pk)


@login_required()
@staff_member_required()
@transaction.atomic
def reorder_tests(request, pk):
    if request.method == 'POST':
        problem = get_object_or_404(Problem, pk=pk)
        new_order: dict = json.loads(request.body)
        try:
            for test_pk, index in new_order.items():
                    int(test_pk)
                    int(index)
        except Exception:
            return HttpResponseBadRequest()
        for test_pk, index in new_order.items():
            test = get_object_or_404(Test, pk=test_pk, problem=problem)
            test.index = index
            test.save()
        return HttpResponse('ok')
    return HttpResponseBadRequest()


@login_required()
@staff_member_required()
@transaction.atomic
def delete_all_tests(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    if request.method == 'POST':
        problem.test_set.all().delete()
        messages.success(request,
                         f"All tests in problem {problem.name} deleted.")
        return redirect('polygon.views.tests', pk=pk)

    return render(request, 'polygon/test/delete_all_tests.html',
                  context={'problem': problem})


class TestGeneratorScriptForm(forms.Form):
    script = forms.CharField(required=True, widget=forms.Textarea)


@login_required()
@staff_member_required()
@transaction.atomic
def generate_tests_from_script(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    form = TestGeneratorScriptForm(request.POST or None)
    if form.is_valid():
        script = form.cleaned_data['script']
        problem.test_generator_script = script

        lines = [i.strip() for i in script.split('\n')]
        command_line_regex = re.compile(r'^([\w]+) (.*) > ([\d]+|\$)$')
        # argument_regex = re.compile(r'".*"|[\S]+')

        occupied_test_indexes = set(problem.test_set.filter(
            use_generator=False).values_list('index', flat=True))
        current_index = 0
        new_tests = []
        for line in lines:
            m = command_line_regex.match(line)
            if not m:
                messages.error(request, 'Invalid script format')
                return redirect('polygon.views.tests', pk=pk)
            generator_name, args, test_index = m.groups()
            if not problem.generator_set.filter(name=generator_name).exists():
                messages.error(request,
                               'Invalid script format: wrong generator name')
                return redirect('polygon.views.tests', pk=pk)
            # arguments = argument_regex.findall(args)
            if test_index == '$':
                while current_index in occupied_test_indexes:
                    current_index += 1
                test_index = current_index
            elif int(test_index) in occupied_test_indexes:
                test_index = int(test_index)
                messages.error(request,
                               f'Invalid script format: test index clash, test #{test_index}')
                return redirect('polygon.views.tests', pk=pk)
            occupied_test_indexes.add(test_index)
            new_tests.append(Test(index=test_index,
                                  data=args,
                                  generator=problem.generator_set.get(
                                      name=generator_name),
                                  use_generator=True,
                                  problem=problem
                                  )
                             )
        problem.test_set.filter(use_generator=True).delete()
        problem.save()
        for test in new_tests:
            test.save()
    else:
        messages.error(request, 'Invalid script format')
    return redirect('polygon.views.tests', pk=pk)


class ImportTestsFromFilesForm(forms.Form):
    tests_files = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}))


@login_required()
@staff_member_required()
@transaction.atomic
def import_tests_from_files(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    form = ImportTestsFromFilesForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        if form.is_valid():
            files = request.FILES.getlist('tests_files')
            files.sort(key=lambda file: file.name)
            for f in files:
                if not str(f.name).isnumeric() and \
                        not re.match(r'^\d+\$?$', f.name):
                    messages.error(request, f'Invalid file name {f.name}')
                    return render(request,
                                  'polygon/test/import_tests_from_files.html',
                                  context={
                                      'form': form,
                                      'problem': problem,
                                  })
            occupied_test_indexes = set(
                problem.test_set.values_list('index', flat=True))
            test_indexes_to_be_added = set()
            current_index = 0
            new_tests = []
            for f in files:
                test_index = f.name
                if re.match(r'^\d+\$$', test_index):
                    while current_index in occupied_test_indexes or current_index in test_indexes_to_be_added:
                        current_index += 1
                    test_index = current_index
                elif int(test_index) in test_indexes_to_be_added:
                    test_index = int(test_index)
                    messages.error(request,
                                   f'Invalid script format: test index clash, test #{test_index}')
                    return redirect('polygon.views.tests', pk=pk)
                test_index = int(test_index)
                if test_index in occupied_test_indexes:
                    # then overwrite
                    new_test = problem.test_set.get(index=test_index)
                    new_test.data = f.read().decode()
                else:
                    new_test = Test(index=test_index,
                                    problem=problem,
                                    data=f.read().decode())
                test_indexes_to_be_added.add(current_index)
                new_tests.append(new_test)
            for test in new_tests:
                test.save()
            messages.success(request,
                             f'Tests from files: {[f.name for f in files]} added')
            return redirect('polygon.views.tests', pk=problem.pk)

    return render(request, 'polygon/test/import_tests_from_files.html',
                  context={
                      'form': form,
                      'problem': problem,
                  })


@login_required()
@staff_member_required()
def change_test_group(request, pk):
    if request.method == 'POST':
        problem = get_object_or_404(Problem, pk=pk)
        # expects {'test_pk': int, 'test_group_pk': int}
        data: dict = json.loads(request.body)
        if 'test_group_pk' not in data or 'test_pk' not in data:
            return HttpResponseBadRequest()
        try:
            int(data['test_pk'])
        except ValueError:
            return HttpResponseBadRequest()
        test = get_object_or_404(Test, pk=data['test_pk'],
                                 problem=problem)
        if data['test_group_pk'] is None:
            test.group = None
        else:
            test_group = get_object_or_404(TestGroup, pk=data['test_group_pk'],
                                           problem=problem)
            test.group = test_group
        test.save()
        return HttpResponse('ok')

    return HttpResponseBadRequest()