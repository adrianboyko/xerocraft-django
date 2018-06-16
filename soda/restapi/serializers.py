
# Standard

# Third Party
from rest_framework import serializers

# Local
import soda.models as sm
import members.models as mm

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = sm.Product
        fields = (
            'id',
            'name',
        )


class VendLogSerializer(serializers.ModelSerializer):

    product = serializers.HyperlinkedRelatedField(
        view_name='soda:product-detail',
        queryset=sm.Product.objects.all(),
        allow_null=True,
        style = {'base_template': 'input.html'},
    )

    who_for = serializers.HyperlinkedRelatedField(
        view_name='memb:member-detail',
        queryset=mm.Member.objects.all(),
        allow_null=True,
        style = {'base_template': 'input.html'},
    )

    class Meta:
        model = sm.VendLog
        fields = (
            'id',
            'when',
            'who_for',
            'product',
        )


