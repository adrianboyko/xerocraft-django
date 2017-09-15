
# Standard
from typing import Type

# Third Party
from rest_framework import serializers

# Local
import members.models as models
from books.models import Sale


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
        'username',
        'friendly_name',
        'is_active',
        'is_currently_paid'
    )

    class MemberSerializer(serializers.ModelSerializer):
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


class WifiMacDetectedSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.WifiMacDetected
        fields = (
            'when',
            'mac',
        )
