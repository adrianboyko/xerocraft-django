
# Standard
from logging import getLogger
from datetime import datetime, timedelta

# Third Party
from django.http import JsonResponse
from django.utils import timezone

# Local
from .models import PlayLogEntry

logger = getLogger("kmkr")


def now_playing(request) -> JsonResponse:

    start = timezone.now()  # type: datetime
    duration = request.GET['DURATION']  # type: str
    title = request.GET['TITLE']  # type: str
    artist = request.GET['ARTIST']  # type: str
    track_id = request.GET['ID']  # type: str
    track_type = request.GET['TYPE']  # type: str

    PlayLogEntry.objects.create(
        start=start,
        duration=duration,
        title=title,
        artist=artist,
        track_id=int(track_id),
        track_type=int(track_type)
    )

    return JsonResponse({"result": "success"})
