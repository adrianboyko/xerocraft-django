
# Standard

# Third Party
from rest_framework import serializers

# Local
import members.models as models
from books.models import Sale


class MembershipSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Membership
        fields = (
            'id',
            'member',
            'membership_type',
            'start_date',
            'end_date',
            # Sale related fields
            'sale',
            'sale_price',
            # ETL related fields
            'ctrlid',
            'protected',
        )


class MembershipGiftCardReferenceSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.MembershipGiftCardReference
        fields = (
            'id',
            'card',
            # Sale related fields
            'sale',
            'sale_price',
            # ETL related fields
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
        )


class WifiMacDetectedSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.WifiMacDetected
        fields = (
            'when',
            'mac',
        )
