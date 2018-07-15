
# Standard

# Third Party
import rest_framework.filters as filters
from django_filters import rest_framework as rf

# Local
from kmkr.models import PlayLogEntry


class PlayLogEntryFilter(rf.FilterSet):
    class Meta:
        model = PlayLogEntry
        fields = {
            'show': [
                'exact'
            ],
            'show_date': [
                'exact'
            ],
        }

