
from .models import PaidMembership
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
            'payment_method',
            'paid_by_member',
            'processing_fee',
            'payment_date',
            'ctrlid',
        )

