
# Standard
from logging import getLogger
from datetime import datetime, timedelta

# Third Party
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
# Local
from .models import PlayLogEntry, Track

logger = getLogger("kmkr")

@csrf_exempt
@require_http_methods(["GET", "POST"])
def now_playing(request) -> JsonResponse:

    if request.method == "GET":

        # TODO: Get should return Show info during times that shows are scheduled.

        aired = PlayLogEntry.objects.latest('start')  # type: PlayLogEntry
        time_remaining = (aired.start + aired.track.duration) - timezone.now()
        if time_remaining.total_seconds() < 0:
            time_remaining = None

        return JsonResponse({
            'id': aired.id,
            'start': aired.start,
            'duration': aired.track.duration,
            'title': aired.track.title,
            'artist': aired.track.artist,
            'radiodj_id': int(aired.track.radiodj_id),
            'track_type': int(aired.track.track_type),
            'time_remaining': time_remaining
        })

    if request.method == "POST":

        # TODO: Posted data should be IGNORED during show times.

        duration = request.POST['DURATION']  # type: str
        if len(duration) == 5:
            # RadioDJ sends MM:SS which Django/Python interprets as HH:MM
            duration = "00:"+duration
        title = request.POST['TITLE']  # type: str
        artist = request.POST['ARTIST']  # type: str
        radiodj_id = int(request.POST['ID'])  # type: int
        track_type = int(request.POST['TYPE'])  # type: int

        track, _ = Track.objects.update_or_create(
            radiodj_id=radiodj_id,
            defaults={
                "duration": duration,
                "title": title,
                "artist": artist,
                "radiodj_id": radiodj_id,
                "track_type": track_type
            }
        )

        PlayLogEntry.objects.create(
            start=timezone.now(),
            track=track
        )
        return JsonResponse({"result": "success"})

