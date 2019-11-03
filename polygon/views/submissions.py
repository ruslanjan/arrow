from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from polygon.judge import judge_submission
from polygon.models import Submission, Problem, SubmissionTestGroupResult


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
                           'Submission': Submission,
                           'test_group_results': submission.submissiontestgroupresult_set.order_by('test_group__index'),
                           'test_results': submission.submissiontestresult_set.order_by('test__index'),
                           'problem': submission.problem})


@login_required()
@staff_member_required()
def view_submissions(request):
    submissions = Submission.objects.all().order_by('-pk')
    paginator = Paginator(submissions,
                          10)  # Show 25 submissions per page
    page = int(request.GET.get('page')) if str(
        request.GET.get('page')).isnumeric() else 1
    return render(request, 'polygon/submission/submissions.html',
                  context={'submissions': paginator.get_page(page),
                           'Submission': Submission,
                           'previous_page': page - 1 if page >= 1 else None,
                           'next_page': page + 1 if page + 1 <= paginator.num_pages else None
                           })


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