from members.models import PaidMembership, Membership, DiscoveryMethod
from books.models import Sale
from rest_framework import serializers


class PaidMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaidMembership
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
        model = Membership
        fields = (
            'id',
            'sale',
            'member',
            'membership_type',
            'family_count',
            'start_date',
            'end_date',
            'ctrlid',
            'protected',
        )


class DiscoveryMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscoveryMethod
        fields = (
            'id',
            'name',
            'order',
        )

