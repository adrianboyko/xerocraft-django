
# Standard

# Third Party
import rest_framework.filters as filters
from django_filters import rest_framework as rf

# Local
from kmkr.models import Episode


class EpisodeFilter(rf.FilterSet):
    class Meta:
        model = Episode
        fields = {
            'show': [
                'exact'
            ],
            'first_broadcast': [
                'exact'
            ],
        }
