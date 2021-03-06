
# Standard

# Third Party
from rest_framework import serializers

# Local
import bzw_ops.models as models


class TimeBlockSerializer(serializers.ModelSerializer):

    types = serializers.HyperlinkedRelatedField(
        view_name='timeblocktype-detail',
        read_only=True,
        many=True,
    )

    class Meta:
        model = models.TimeBlock
        fields = (
            'id',
            'is_now',
            'start_time',
            'duration',
            'first',
            'second',
            'third',
            'fourth',
            'last',
            'every',
            'monday',
            'tuesday',
            'wednesday',
            'thursday',
            'friday',
            'saturday',
            'sunday',
            'types',
        )


class TimeBlockTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.TimeBlockType
        fields = (
            'id',
            'name',
            'description',
            'is_default',
        )

