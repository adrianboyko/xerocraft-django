
# Standard

# Third Party
import rest_framework.filters as filters
from django_filters import rest_framework as rf

# Local
from kmkr.models import ShowInstance

class ShowInstanceFilter(rf.FilterSet):
    class Meta:
        model = ShowInstance
        fields = {
            'show': [
                'exact'
            ],
            'date': [
                'exact'
            ],
        }
