from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from polygon.models import Problem


@login_required()
@staff_member_required()
def index(request):
    problems = Problem.objects.all().order_by('-pk')
    paginator = Paginator(problems,
                          16)  # Show 25 submissions per page
    page = int(request.GET.get('page')) if str(
        request.GET.get('page')).isnumeric() else 1
    return render(request, 'polygon/index.html', context={
        'problems': paginator.get_page(page),
        'previous_page': page - 1 if page >= 1 else None,
        'next_page': page + 1 if page + 1 <= paginator.num_pages else None
    })


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


@login_required()
@staff_member_required()
def clear_problem_cache(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    problem.solution_compiled = None
    problem.checker_compiled = None
    problem.interactor_compiled = None
    problem.save()
    for generator in problem.generator_set.all():
        generator.generator_compiled = None
        generator.save()
    return redirect('polygon.views.problem', pk=pk)


class ProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = (
            'name', 'time_limit', 'memory_limit', 'solution', 'checker',
            'interactor', 'is_active', 'is_interactive', 'is_graded',
            'is_sub_task')


@login_required()
@staff_member_required()
def view_problem(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    form = ProblemForm(request.POST or None, instance=problem)
    if request.method == 'POST':
        if form.is_valid():
            if form.cleaned_data['is_graded'] and form.cleaned_data['is_sub_task']:
                messages.error(request, f'You can not make problem is_graded '
                                        f'and is_sub_task at the same time')
            else:
                form.save()
                messages.success(request, f'Problem "{problem.name}" saved!')
    return render(request, 'polygon/problem/problem.html',
                  context={'problem': problem, 'form': form})
