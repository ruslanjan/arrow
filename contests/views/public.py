from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

from contests.models import Contest


def index(request):
    contests = Contest.objects.filter(is_public=True, is_launched=True).filter(
        Q(start_date_time__gte=timezone.now()) |
        Q(is_ended=False, is_started=True))
    past_contests = Contest.objects.filter(is_public=True,
                                           is_ended=True,
                                           is_launched=True)
    return render(request, 'contests/index.html', {
        'current_contests': contests,
        'past_contests': past_contests,
    })
