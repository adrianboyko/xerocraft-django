
# Standard

# Third Party
import rest_framework.filters as filters

# Local
from members.models import Member


class HasRfidNumFilterBackend(filters.BaseFilterBackend):
    """
    Filter that exposes only members with a certain cardnum.
    For use on MembersViewSet.
    """
    def filter_queryset(self, request, queryset, view):
        rfidnum = request.query_params.get('rfidnum', None)
        m = Member.get_by_card_str(rfidnum)
        return queryset.filter(membership_card_md5=m.membership_card_md5)