
# Standard
from typing import Type
from datetime import date

# Third Party
from rest_framework import serializers

# Local
import members.models as models


def get_MemberSerializer(respect_privacy: bool) -> Type[serializers.ModelSerializer]:

    private_fields = (
        'first_name',
        'last_name',
        'email',
    )

    if respect_privacy:
        private_fields = ()

    public_fields = (
        'id',
        'auth_user',
        'username',
        'friendly_name',
        'is_active',
        'is_currently_paid',  # TODO: Remove this and add "is_current" to Membership serialization.
        'latest_nonfuture_membership'
    )

    class MemberSerializer(serializers.ModelSerializer):

        latest_nonfuture_membership = MembershipSerializer(many=False, read_only=True)

        class Meta:
            model = models.Member
            fields = private_fields + public_fields

    return MemberSerializer


class MembershipSerializer(serializers.ModelSerializer):
    member = serializers.HyperlinkedRelatedField(read_only=True, view_name='memb:member-detail')

    class Meta:
        model = models.Membership
        fields = (
            'id',
            'member',
            'membership_type',
            'start_date',
            'end_date',
            # Sale related fields:
            'sale',
            'sale_price',
            # ETL related fields:
            'ctrlid',
            'protected',
        )


class MembershipGiftCardReferenceSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.MembershipGiftCardReference
        fields = (
            'id',
            'card',
            # Sale related fields:
            'sale',
            'sale_price',
            # ETL related fields:
            'ctrlid',
            'protected',
        )


class DiscoveryMethodSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.DiscoveryMethod
        fields = (
            'id',
            'name',
            'order',
            'visible'
        )


class VisitEventSerializer(serializers.ModelSerializer):

    who_embed = get_MemberSerializer(True)(many=False, read_only=True, source='who')

    who = serializers.HyperlinkedRelatedField(
        read_only=False,
        view_name='memb:member-detail',
        queryset=models.Member.objects.all()
    )

    class Meta:
        model = models.VisitEvent
        fields = (
            'id',
            'who',
            'who_embed',
            'when',
            'event_type',
            'reason',
            'method'
        )