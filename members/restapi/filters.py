
# Standard

# Third Party
import rest_framework.filters as filters
from django_filters import rest_framework as rf

# Local
from members.models import Member, VisitEvent


class HasRfidNumFilterBackend(filters.BaseFilterBackend):
    """
    Filter that exposes only members with a certain cardnum.
    For use on MembersViewSet.
    """
    def filter_queryset(self, request, queryset, view):
        rfidnum = request.query_params.get('rfidnum', None)
        if rfidnum is None:
            return queryset
        else:
            m = Member.get_by_card_str(rfidnum)
            return queryset.filter(membership_card_md5=m.membership_card_md5)


class MemberFilter(rf.FilterSet):
    class Meta:
        model = Member
        fields = {
            'auth_user__username': [
                'iexact',
                'icontains',
                'istartswith',
            ],
            'auth_user__last_name': [
                'iexact',
                'istartswith',
            ],
            'auth_user__is_active': [
                'exact',
            ],
        }


class VisitEventFilter(rf.FilterSet):
    class Meta:
        model = VisitEvent
        fields = {
            'when': [
                'gte',
            ],
            'event_type': [
                'exact',
            ],
            'method': [
                'exact',
            ],
            'who__auth_user__username': [
                'iexact',
            ],
        }
