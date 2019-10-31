from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from polygon.models import Problem, Generator, ProblemFile

@login_required()
@staff_member_required()
def view_files(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    return render(request, 'polygon/problem/files/files.html', context={
        'problem': problem,
        'files': problem.problemfile_set.order_by('-pk')
    })


class ProblemFileCreationForm(forms.ModelForm):
    class Meta:
        model = ProblemFile
        fields = ('file',)


@login_required()
@staff_member_required()
def upload_file(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    form = ProblemFileCreationForm(request.POST or None, request.FILES)
    if form.is_valid():
        problem_file: ProblemFile = form.save(commit=False)
        problem_file.problem = problem
        problem_file.save()
        messages.success(request, 'File uploaded!')
        return redirect('polygon.views.files', pk=pk)
    return render(request, 'polygon/problem/files/upload_file.html', context={
        'problem': problem,
        'form': form
    })


@login_required()
@staff_member_required()
def delete_file(request, problem_id, pk):
    problem = get_object_or_404(Problem, pk=problem_id)
    problem_file = get_object_or_404(ProblemFile, pk=pk, problem=problem)
    problem_file.delete()
    messages.success(request, 'File deleted!')
    return redirect('polygon.views.files', pk=problem_id)
