from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.shortcuts import render, redirect, get_object_or_404

from .models import Problem, Statement, Test


@login_required()
@staff_member_required()
def index(request):
    problems = Problem.objects.all()
    return render(request, 'polygon/index.html', context={'problems': problems})


class DeleteProblemForm(forms.Form):
    name = forms.CharField(max_length=128, required=True)


@login_required()
@staff_member_required()
def delete_problem(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    form = DeleteProblemForm(request.POST)
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
    form = CreateProblemForm(request.POST)
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
            'name', 'solution', 'checker', 'is_ready')


@login_required()
@staff_member_required()
def view_problem(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    form = ProblemForm(request.POST, instance=problem)
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
        return redirect('polygon.views.problem', pk=problem_id)

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
    form = StatementForm(request.POST, request.FILES, instance=statement)
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
                  context={'problem': problem})


class CreateTestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ('index', 'data')


@login_required()
@staff_member_required()
def create_test(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    next_test_index = Test.objects.aggregate(Max('index'))

    form = CreateTestForm(request.POST or None, initial={
        'index': next_test_index['index__max'] + 1 if next_test_index[
            'index__max'] else 0})
    if request.method == 'POST':
        if form.is_valid():
            test = form.save(commit=False)
            test.problem = problem
            test.save()
            return redirect('polygon.views.test',
                            problem_id=problem.pk, pk=test.pk)

    return render(request, 'polygon/test/create_test.html',
                  context={'form': form, 'problem': problem})


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
    return redirect('polygon.views.problem', pk=problem_id)


class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ('index', 'data')


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

    return render(request, 'polygon/test/test.html',
                  context={'form': form, 'test': test,
                           'problem': problem})


# Tests
# ==============================================================================
# Test Submission
def test_submission(request, pk):
    form = None
    problem = get_object_or_404(Problem, pk=pk)
    return render(request, 'polygon/problem/test_submission.html',
                  context={'form': form, 'problem': problem})