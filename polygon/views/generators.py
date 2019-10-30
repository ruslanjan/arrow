from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from polygon.models import Problem, Generator


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
    save_and_exit = forms.BooleanField(required=False)

    class Meta:
        model = Generator
        fields = ('generator', 'name')


@login_required()
@staff_member_required()
def view_generator(request, problem_id, pk):
    problem = get_object_or_404(Problem, pk=problem_id)
    generator = get_object_or_404(Generator, pk=pk, problem=problem)
    form = GeneratorForm(request.POST or None, instance=generator)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f'Generator "{generator.name}" saved')
            if form.cleaned_data['save_and_exit']:
                return redirect('polygon.views.generators', pk=problem_id)

    return render(request, 'polygon/generator/generator.html',
                  context={'form': form, 'generator': generator,
                           'problem': problem})

