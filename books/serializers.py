from .models import Sale, SaleNote
from .models import Donation, DonationNote, MonetaryDonation, PhysicalDonation
from rest_framework import serializers


class SaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sale
        fields = (
            'id',
            'sale_date',
            'payer_name',
            'payer_email',
            'payment_method',
            'method_detail',
            'total_paid_by_customer',
            'processing_fee',
            'ctrlid',
            'protected',
        )


class SaleNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleNote
        fields = (
            'id',
            'author',
            'content',
            'sale',
        )


class DonationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donation
        fields = (
            'id',
            'donation_date',
            'donator_name',
            'donator_email',
        )


class DonationNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonationNote
        fields = (
            'id',
            'author',
            'content',
            'donation',
        )


class MonetaryDonationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonetaryDonation
        fields = (
            'id',
            'donation',
            'sale',
            'amount',
            'ctrlid',
            'protected',
        )


class PhysicalDonationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonetaryDonation
        fields = (
            'id',
            'donation',
            'value',
            'description',
        )
