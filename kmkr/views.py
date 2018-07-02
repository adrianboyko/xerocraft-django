
# Standard
from logging import getLogger
from datetime import datetime, timedelta

# Third Party
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_GET
# Local
from .models import PlayLogEntry

logger = getLogger("kmkr")

@csrf_exempt
@require_http_methods(["GET", "POST"])
def now_playing(request) -> JsonResponse:

    start = timezone.now()  # type: datetime

    if request.method == "GET":
        duration = request.GET['DURATION']  # type: str
        title = request.GET['TITLE']  # type: str
        artist = request.GET['ARTIST']  # type: str
        track_id = request.GET['ID']  # type: str
        track_type = request.GET['TYPE']  # type: str

    if request.method == "POST":
        duration = request.POST['DURATION']  # type: str
        title = request.POST['TITLE']  # type: str
        artist = request.POST['ARTIST']  # type: str
        track_id = request.POST['ID']  # type: str
        track_type = request.POST['TYPE']  # type: str

    if len(duration) == 5:
        # RadioDJ sends MM:SS which Django/Python interprets as HH:MM
        duration += "00:"+duration

    PlayLogEntry.objects.create(
        start=start,
        duration=duration,
        title=title,
        artist=artist,
        track_id=int(track_id),
        track_type=int(track_type)
    )

    return JsonResponse({"result": "success"})


@require_GET
def now_playing_info(request) -> JsonResponse:
    ple = PlayLogEntry.objects.latest('start')
    time_remaining = (ple.start + ple.duration) - timezone.now()
    if time_remaining.total_seconds() < 0:
        time_remaining = None
    return JsonResponse({
        'id': ple.id,
        'start': ple.start,
        'duration': ple.duration,
        'title': ple.title,
        'artist': ple.artist,
        'track_id': int(ple.track_id),
        'track_type': int(ple.track_type),
        'time_remaining': time_remaining
    })
