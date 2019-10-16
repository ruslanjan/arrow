import re

from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Max
from django.shortcuts import render, redirect, get_object_or_404

from .judge import judge_submission
from .models import Problem, Statement, Test, Submission, Generator


@login_required()
@staff_member_required()
def index(request):
    problems = Problem.objects.all().order_by('-pk')
    return render(request, 'polygon/index.html', context={'problems': problems})


class DeleteProblemForm(forms.Form):
    name = forms.CharField(max_length=128, required=True)


@login_required()
@staff_member_required()
def delete_problem(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    form = DeleteProblemForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            if form.cleaned_data['name'] == problem.name:
                problem.delete()
                messages.success(request, f"problem {problem.name} deleted.")
                return redirect('polygon.views.index')
            else:
                messages.error(request, 'names don\'t match')

    return render(request, 'polygon/problem/delete_problem.html',
                  context={'form': form, 'problem': problem})


class CreateProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = ('name',)


@login_required()
@staff_member_required()
def create_problem(request):
    form = CreateProblemForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            new_problem = form.save()
            return redirect('polygon.views.problem', pk=new_problem.pk)

    return render(request, 'polygon/problem/create_problem.html',
                  context={'form': form})


class ProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = (
            'name', 'time_limit', 'memory_limit', 'solution', 'checker',
            'is_active')


@login_required()
@staff_member_required()
def view_problem(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    form = ProblemForm(request.POST or None, instance=problem)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
    return render(request, 'polygon/problem/problem.html',
                  context={'problem': problem, 'form': form})


# Problem
# ==============================================================================
# Statements

@login_required()
@staff_member_required()
def view_statements(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    return render(request, 'polygon/statement/statements.html',
                  context={'problem': problem})


class CreateStatementForm(forms.ModelForm):
    class Meta:
        model = Statement
        fields = ('name',)


@login_required()
@staff_member_required()
def create_statement(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    form = CreateStatementForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            statement = form.save(commit=False)
            statement.problem = problem
            statement.save()
            return redirect('polygon.views.statement',
                            problem_id=problem.pk, pk=statement.pk)

    return render(request, 'polygon/statement/create_statement.html',
                  context={'form': form, 'problem': problem})


@login_required()
@staff_member_required()
def delete_statement(request, problem_id, pk):
    problem = get_object_or_404(Problem, pk=problem_id)
    statement = get_object_or_404(Statement, pk=pk)
    if statement.problem.pk != problem_id:
        messages.error(request, f"statement do not belongs to given problem.")
        return redirect('polygon.views.index')
    if request.method == 'POST':
        statement.delete()
        messages.success(request, f"Statement {statement.name} deleted.")
        return redirect('polygon.views.statements', pk=problem_id)

    return render(request, 'polygon/statement/delete_statement.html',
                  context={'problem': problem, 'statement': statement})


class StatementForm(forms.ModelForm):
    class Meta:
        model = Statement
        fields = (
            'name', 'pdf_statement')


@login_required()
@staff_member_required()
def view_statement(request, problem_id, pk):
    problem = get_object_or_404(Problem, pk=problem_id)
    statement = get_object_or_404(Statement, pk=pk)
    form = StatementForm(request.POST or None, request.FILES,
                         instance=statement)
    if statement.problem.pk != problem_id:
        messages.error(request, f"statement do not belongs to given problem.")
        return redirect('polygon.views.index')
    if request.method == 'POST':
        if form.is_valid():
            form.save()

    return render(request, 'polygon/statement/statement.html',
                  context={'form': form, 'statement': statement,
                           'problem': problem})


# Statements
# ==============================================================================
# Tests

@login_required()
@staff_member_required()
def view_tests(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    return render(request, 'polygon/test/tests.html',
                  context={'problem': problem,
                           'tests': problem.test_set.all().order_by('index')})


class CreateTestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ('index', 'data', 'use_generator', 'generator', 'is_example',
                  'example_answer')


@login_required()
@staff_member_required()
def create_test(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    next_test_index = Test.objects.filter(problem=problem).aggregate(Max('index'))

    form = CreateTestForm(request.POST or None, initial={
        'index': next_test_index['index__max'] + 1 if next_test_index[
            'index__max'] is not None else '0'})
    if request.method == 'POST':
        if form.is_valid():
            if form.cleaned_data['use_generator'] \
                    and form.cleaned_data['is_example']:
                messages.error(request, 'Test can not use generator '
                                        'and be example at the same time!')
            else:
                test = form.save(commit=False)
                test.problem = problem
                test.save()
                return redirect('polygon.views.test',
                                problem_id=problem.pk, pk=test.pk)

    return render(request, 'polygon/test/create_test.html',
                  context={'form': form,
                           'generators': Generator.objects.filter(
                               problem=problem),
                           'problem': problem})


@login_required()
@staff_member_required()
def delete_test(request, problem_id, pk):
    problem = get_object_or_404(Problem, pk=problem_id)
    test = get_object_or_404(Test, pk=pk)
    if test.problem.pk != problem_id:
        messages.error(request, f"test do not belongs to given problem.")
        return redirect('polygon.views.index')
    test.delete()
    messages.success(request,
                     f"test {test.index} from problem {problem.name} deleted.")
    return redirect('polygon.views.tests', pk=problem_id)


class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ('index', 'data', 'use_generator', 'generator', 'is_example',
                  'example_answer')


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
            if form.cleaned_data['use_generator'] \
                    and form.cleaned_data['is_example']:
                messages.error(request, 'Test can not use generator '
                                        'and be example at the same time!')
            else:
                form.save()

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


class TestGeneratorScriptForm(forms.Form):
    script = forms.CharField(required=True, widget=forms.Textarea)


@login_required()
@staff_member_required()
@transaction.atomic
def generate_tests_from_script(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    tests = problem.test_set.all().order_by('index')
    form = TestGeneratorScriptForm(request.POST or None)
    if form.is_valid():
        script = form.cleaned_data['script']
        problem.test_generator_script = script

        lines = [i.strip() for i in script.split('\n')]
        command_line_regex = re.compile(r'^([\w]+) (.*) > ([\d]+|\$)$')
        # argument_regex = re.compile(r'".*"|[\S]+')

        occupied_test_indexes = set(i.index for i in Test.objects.filter(
            use_generator=False).only('index'))
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
        Test.objects.filter(use_generator=True).delete()
        problem.save()
        for test in new_tests:
            test.save()
    else:
        messages.error(request, 'Invalid script format')
    return redirect('polygon.views.tests', pk=pk)


# Tests
# ==============================================================================
# Generators

@login_required()
@staff_member_required()
def view_generators(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    return render(request, 'polygon/generator/generators.html',
                  context={'problem': problem,
                           'generators': problem.generator_set.all()})


class CreateGeneratorForm(forms.ModelForm):
    class Meta:
        model = Generator
        fields = ('name',)


@login_required()
@staff_member_required()
def create_generator(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    form = CreateGeneratorForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            generator = form.save(commit=False)
            if problem.generator_set.filter(name=generator.name).exists():
                messages.error(request,
                               f"Generator with that name exists.")
            else:
                generator.problem = problem
                generator.save()
                return redirect('polygon.views.generator', problem_id=pk,
                                pk=generator.pk)

    return render(request, 'polygon/generator/create_generator.html',
                  context={'form': form, 'problem': problem})


@login_required()
@staff_member_required()
def delete_generator(request, problem_id, pk):
    problem = get_object_or_404(Problem, pk=problem_id)
    generator = get_object_or_404(Generator, pk=pk)
    if generator.problem.pk != problem_id:
        messages.error(request, f"Generator do not belongs to given problem.")
        return redirect('polygon.views.index')
    generator.delete()
    messages.success(request,
                     f"Generator {generator.name} from problem {problem.name} deleted.")
    return redirect('polygon.views.problem', pk=problem_id)


class GeneratorForm(forms.ModelForm):
    class Meta:
        model = Generator
        fields = ('generator', 'name')


@login_required()
@staff_member_required()
def view_generator(request, problem_id, pk):
    generator = get_object_or_404(Generator, pk=pk)
    problem = get_object_or_404(Problem, pk=problem_id)
    if generator.problem.pk != problem_id:
        messages.error(request, f"Generator do not belongs to given problem.")
        return redirect('polygon.views.index')
    form = GeneratorForm(request.POST or None, instance=generator)
    if request.method == 'POST':
        if form.is_valid():
            form.save()

    return render(request, 'polygon/generator/generator.html',
                  context={'form': form, 'generator': generator,
                           'problem': problem})


# Generators
# ==============================================================================
# Test Submission

class TestSubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ('data', 'submission_type')


@login_required()
@staff_member_required()
def test_submission(request, pk):
    form = TestSubmissionForm(request.POST or None)
    problem = get_object_or_404(Problem, pk=pk)
    if request.method == 'POST':
        if form.is_valid():
            submission = form.save(commit=False)
            submission.problem = problem
            submission.user = request.user
            submission.save()
            judge_submission(submission)
            return redirect('polygon.views.submission', pk=submission.pk)
    return render(request,
                  'polygon/problem/test_submission.html',
                  context={'form': form, 'problem': problem,
                           'Submission': Submission})


@login_required()
@staff_member_required()
def view_submission(request, pk):
    submission = get_object_or_404(Submission, pk=pk)
    return render(request,
                  'polygon/submission/submission.html',
                  context={'submission': submission,
                           'problem': submission.problem})


@login_required()
@staff_member_required()
def view_submissions(request):
    submissions = Submission.objects.all().order_by('-pk')
    return render(request, 'polygon/submission/submissions.html',
                  context={'submissions': submissions, 'Submission': Submission})

@staff_member_required()
def rejudge_submission(request, pk):
    submission = get_object_or_404(Submission, pk=pk)
    judge_submission(submission)
    return redirect('polygon.views.submission', pk=pk)


@login_required()
@staff_member_required()
def rejudge_submissions(request):
    for submission in Submission.objects.all():
        judge_submission(submission)
        # problem = submission.problem
        # (judge_submission.s(submission.pk, 0) | run_sandbox.s() | parse_sandbox_result.s(submission.pk, 0)).apply_async()
        # chord((judge_submission.s(submission.pk, test.pk) | run_sandbox.s() | parse_sandbox_result.s(submission.pk, test.pk)) for test in problem.test_set.all())(apply_submission_result.s(submission.pk))

    return redirect('polygon.views.submissions')