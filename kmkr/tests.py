
# Standard
from datetime import timedelta, time, datetime, date

# Third-Party
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

# Local
from .models import (
    PlayLogEntry, Track, Show, ShowTime, OnAirPersonality
)


class TestNowPlaying(TestCase):

    tz = timezone.get_current_timezone()

    url = reverse('kmkr:now-playing')

    data1 = {
        "TITLE": "Spam It",
        "ARTIST": "The Spammers",
        "ID": 999,
        "TYPE": Track.TYPE_JINGLE,
        "DURATION": "03:33"
    }

    def test_track_add_get_update_get(self):

        client = Client()

        response = client.post(self.url, self.data1)
        self.assertEqual(response.status_code, 200)

        response = client.get(self.url)
        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertEqual(json['track']['title'], self.data1['TITLE'])
        self.assertEqual(json['track']['artist'], self.data1['ARTIST'])
        self.assertEqual(json['track']['radiodj_id'], self.data1['ID'])
        self.assertEqual(json['track']['track_type'], self.data1['TYPE'])

        # Simulate the case where the title is updated in RadioDJ:
        data2 = {
            "TITLE": "xxxxxxxxx",
            "ARTIST": self.data1['ARTIST'],
            "ID": self.data1['ID'],
            "TYPE": self.data1['TYPE'],
            "DURATION": self.data1['DURATION'],
        }

        response = client.post(self.url, data2)
        self.assertEqual(response.status_code, 200)

        response = client.get(self.url)
        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertEqual(json['track']['title'], data2['TITLE'])  # The field that changed
        self.assertEqual(json['track']['artist'], self.data1['ARTIST'])
        self.assertEqual(json['track']['radiodj_id'], self.data1['ID'])
        self.assertEqual(json['track']['track_type'], self.data1['TYPE'])

    def test_current_show(self):

        client = Client()

        show = Show.objects.create(
            title="Bob's Show",
            description="Bob talks about stuff",
            duration=timedelta(hours=1)
        )
        showtime = ShowTime.objects.create(
            show=show,
            mondays=True,
            start_time=time(14, 00, 00)
        )

        dt = timezone.make_aware(datetime(2018, 7, 9, 14, 30, 00), self.tz)  # This is a Monday

        # Should be current at dt
        with freeze_time(dt):
            response = client.get(self.url)
            self.assertEqual(response.status_code, 200)
            json = response.json()
            self.assertIsNotNone(json['show'])
            self.assertEqual(json['show']['title'], show.title)

        # Should NOT be current at dt + 3hrs
        with freeze_time(dt+timedelta(hours=3)):
            response = client.get(self.url)
            self.assertEqual(response.status_code, 200)
            json = response.json()
            self.assertIsNone(json['show'])

        # should NOT be current at dt + 24hours
        with freeze_time(dt+timedelta(hours=24)):
            response = client.get(self.url)
            self.assertEqual(response.status_code, 200)
            json = response.json()
            self.assertIsNone(json['show'])


class TestPlayTimeDeduction(TestCase):

    tz = timezone.get_current_timezone()

    url = reverse('kmkr:now-playing')

    data1 = {
        "TITLE": "The Show, Episode 1",
        "ARTIST": "The Host",
        "ID": 999,
        "TYPE": Track.TYPE_OTHER,
        "DURATION": "1:00:00"
    }

    def test1(self):

        user = User.objects.create(
            username="host"
        )

        oap = OnAirPersonality.objects.create(
            member=user.member
        )

        show = Show.objects.create(
            title="The Show"
        )
        show.hosts.add(oap)

        client = Client()

        response = client.post(self.url, self.data1)
        self.assertEqual(response.status_code, 200)


