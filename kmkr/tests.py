
# Standard
from datetime import timedelta

# Third-Party
from django.test import TestCase, Client
from django.urls import reverse

# Local
from .models import PlayLogEntry, Track


class TestNowPlaying(TestCase):

    def test_post_and_immediate_get(self):
        client = Client()

        url = reverse('kmkr:now-playing')
        data = {
            "TITLE": "Spam It",
            "ARTIST": "The Spammers",
            "ID": 999,
            "TYPE": Track.TYPE_JINGLE,
            "DURATION": "03:33"
        }
        response = client.post(url, data)
        self.assertEqual(response.status_code, 200)

        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], data['TITLE'])
        self.assertEqual(response.json()['artist'], data['ARTIST'])
        self.assertEqual(response.json()['radiodj_id'], data['ID'])
        self.assertEqual(response.json()['track_type'], data['TYPE'])
