from .models import *
from rest_framework import serializers


class SaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sale
        fields = (
            'id',
            'sale_date',
            'deposit_date',
            'payer_name',
            'payer_email',
            'payment_method',
            'method_detail',
            'total_paid_by_customer',
            'processing_fee',
            'fee_payer',
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
            'sale',
            'amount',
            'earmark',
            'ctrlid',
            'protected',
        )


class OtherItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtherItem
        fields = (
            'id',
            'type',
            'sale',
            'sale_price',
            'qty_sold',
            'ctrlid',
            'protected',
        )


class OtherItemTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtherItemType
        fields = (
            'id',
            'name',
            'description',
        )