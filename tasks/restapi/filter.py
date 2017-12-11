

# Standard

# Third Party
from django_filters import rest_framework as filters

# Local
from tasks.models import Work


class WorkFilter(filters.FilterSet):
    class Meta:
        model = Work
        fields = {
            'claim': ['exact'],
            'work_duration': ['isnull']
        }
