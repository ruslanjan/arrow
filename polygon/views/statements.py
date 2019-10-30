from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from polygon.models import Problem, Statement


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
    save_and_exit = forms.BooleanField(required=False)

    class Meta:
        model = Statement
        fields = (
            'name', 'is_default', 'is_visible', 'only_pdf', 'pdf_statement',
            'problem_name',
            'legend', 'input_format', 'output_format', 'notes', 'interaction',
            'scoring', 'tutorial')


@login_required()
@staff_member_required()
def view_statement(request, problem_id, pk):
    problem = get_object_or_404(Problem, pk=problem_id)
    statement = get_object_or_404(Statement, pk=pk, problem=problem)
    form = StatementForm(request.POST or None, request.FILES or None,
                         instance=statement)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f'Statement "{statement.name}" saved')
            if form.cleaned_data['save_and_exit']:
                return redirect('polygon.views.statements', pk=problem_id)
        else:
            messages.error(request, 'Invalid form')

    return render(request, 'polygon/statement/statement.html',
                  context={'form': form, 'statement': statement,
                           'problem': problem})


@login_required()
@staff_member_required()
def preview_statement(request, problem_id, pk):
    problem = get_object_or_404(Problem, pk=problem_id)
    statement = get_object_or_404(Statement, pk=pk, problem=problem)
    return render(request, 'polygon/statement/preview_statement.html',
                  context={'statement': statement,
                           'problem': problem})
