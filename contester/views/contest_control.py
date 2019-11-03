from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from contester.models import Contest


@staff_member_required
@login_required
def contest_control_panel(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    return render(request, 'contester/contest/contest_control_panel.html', {
        'contest': contest
    })


@staff_member_required
@login_required
def launch_contest(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    contest.is_launched = True
    contest.save()
    messages.success(request, f'Contest "{contest.name}" launched')
    return redirect('contester.views.contest_control_panel', pk=contest.pk)


@staff_member_required
@login_required
def abort_contest(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    contest.is_launched = False
    contest.is_ended = False
    contest.is_started = False
    contest.save()
    messages.success(request, f'Contest "{contest.name}" Aborted!')
    return redirect('contester.views.contest_control_panel', pk=contest.pk)


@staff_member_required
@login_required
def start_contest(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    contest.start_date_time = timezone.now()
    contest.save()
    messages.success(request, f'Contest "{contest.name}" started')
    return redirect('contester.views.contest_control_panel', pk=contest.pk)


@staff_member_required
@login_required
def stop_contest(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    contest.is_ended = True
    contest.save()
    messages.success(request, f'Contest "{contest.name}" ended')
    return redirect('contester.views.contest_control_panel', pk=contest.pk)
