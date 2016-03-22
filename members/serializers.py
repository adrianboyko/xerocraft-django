import members.models as models
from books.models import Sale
from rest_framework import serializers


class PaidMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PaidMembership
        fields = (
            'id',
            'membership_type',
            'family_count',
            'start_date',
            'end_date',
            'payer_name',
            'payer_email',
            'payer_notes',
            'payment_method',
            'paid_by_member',
            'processing_fee',
            'payment_date',
            'ctrlid',
            'protected',
        )


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

