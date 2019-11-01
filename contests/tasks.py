from django.utils import timezone

from arrow.celery import app
from .models import Contest


@app.task()
def update_contest_status():
    print('Contest update')
    contests = Contest.objects.filter(is_launched=True, is_ended=False)
    for contest in contests:
        if not contest.is_started and timezone.now() >= contest.start_date_time:
            contest.is_started = True
            contest.save()
        elif timezone.now() >= contest.start_date_time + timezone.timedelta(
                seconds=contest.duration):
            contest.is_ended = True
            contest.save()
