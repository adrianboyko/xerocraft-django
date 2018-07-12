
# Standard
from logging import getLogger
from datetime import datetime, timedelta
from typing import Tuple, Optional

# Third Party
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

# Local
from .models import PlayLogEntry, Track, Show, ShowTime, OnAirPersonality

logger = getLogger("kmkr")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def now_playing(request) -> JsonResponse:

    tznow = timezone.now()  # Get current time ASAP.

    if request.method == "GET":

        showdata = None
        show = Show.current_show()  # type: Show
        if show is not None:
            showtime = show.current_showtime()
            showdata = {
                'title': show.title,
                'hosts': [x.moniker for x in show.hosts.all()],
                'start_time': showtime.start_time,
                'duration_seconds': round(show.duration.total_seconds(), 1),
            }

        trackdata = None
        try:
            ple = PlayLogEntry.objects.latest('start')  # type: PlayLogEntry
            time_remaining = (ple.start + ple.track.duration) - tznow  # type: timedelta
            trackdata = {
                'title': ple.track.title,
                'artist': ple.track.artist,
                'radiodj_id': int(ple.track.radiodj_id),
                'track_type': int(ple.track.track_type),
                'start_datetime': ple.start,
                'duration_seconds': round(ple.track.duration.total_seconds(), 1),
                'remaining_seconds': round(time_remaining.total_seconds(), 1)
            }
        except PlayLogEntry.DoesNotExist:
            pass  # trackdata is already None

        return JsonResponse({'show': showdata, 'track': trackdata})

    if request.method == "POST":

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

        currentshow = Show.current_show()
        if currentshow is None:
            # Only create the play log entry if there's no show scheduled for this time.
            # Reason: KMKR leaves RadioDJ running during their live shows, but faded out.
            PlayLogEntry.objects.create(
                start=tznow,
                track=track
            )
        else:
            logger.info("Did not log {} because {} is airing.".format(track, currentshow.title))

        return JsonResponse({"result": "success"})


@csrf_exempt
@require_http_methods(["GET", "POST"])
def now_playing_fbapp(request) -> HttpResponse:
    aired = PlayLogEntry.objects.latest('start')  # type: PlayLogEntry
    time_remaining = (aired.start + aired.track.duration) - timezone.now()
    response = HttpResponse()
    response['X-Frame-Options'] = "ALLOW-FROM https://www.facebook.com/"
    if time_remaining.total_seconds() > 0:
        response.write(str(aired.track))
    else:
        response.write("Sorry, no information available.")
    return response


@require_http_methods(["GET"])
def now_playing_fbapp_privacy_policy(request) -> HttpResponse:
    return HttpResponse("This app does not collect any personal information.")
