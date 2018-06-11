
# Standard

# Third Party
from rest_framework import serializers

# Local
import soda.models as sm
import members.models as mm


class VendLogSerializer(serializers.ModelSerializer):

    # product = serializers.HyperlinkedRelatedField(
    #     view_name='soda:product-detail',
    #     queryset=sm.Product.objects.all(),
    #     allow_null=True,
    #     style = {'base_template': 'input.html'},
    # )

    class Meta:
        model = sm.VendLog
        fields = (
            'id',
            'who_for',
            'product',
        )


