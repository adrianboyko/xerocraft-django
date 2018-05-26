

# Standard

# Third Party
from django_filters import rest_framework as filters

# Local
from tasks.models import Work, Play


class WorkFilter(filters.FilterSet):
    class Meta:
        model = Work
        fields = {
            'claim': ['exact'],
            'work_duration': ['isnull']
        }


class PlayFilter(filters.FilterSet):
    class Meta:
        model = Play
        fields = {
            'playing_member': ['exact'],
            'play_date': ['exact'],
            'play_duration': ['isnull'],
        }
