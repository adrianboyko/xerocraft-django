
# Standard
from datetime import timedelta

# Third-Party
from django.test import TestCase, Client
from django.urls import reverse

# Local
from .models import PlayLogEntry, Track


class TestNowPlaying(TestCase):

    def test_post_and_get(self):
        client = Client()

        url = reverse('kmkr:now-playing')

        data1 = {
            "TITLE": "Spam It",
            "ARTIST": "The Spammers",
            "ID": 999,
            "TYPE": Track.TYPE_JINGLE,
            "DURATION": "03:33"
        }
        response = client.post(url, data1)
        self.assertEqual(response.status_code, 200)

        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], data1['TITLE'])
        self.assertEqual(response.json()['artist'], data1['ARTIST'])
        self.assertEqual(response.json()['radiodj_id'], data1['ID'])
        self.assertEqual(response.json()['track_type'], data1['TYPE'])

        # Simulate the case where the title is updated in RadioDJ:
        data2 = {
            "TITLE": "xxxxxxxxx",
            "ARTIST": data1['ARTIST'],
            "ID": data1['ID'],
            "TYPE": data1['TYPE'],
            "DURATION": data1['DURATION'],
        }

        response = client.post(url, data2)
        self.assertEqual(response.status_code, 200)

        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], data2['TITLE'])  # The field that changed
        self.assertEqual(response.json()['artist'], data1['ARTIST'])
        self.assertEqual(response.json()['radiodj_id'], data1['ID'])
        self.assertEqual(response.json()['track_type'], data1['TYPE'])
