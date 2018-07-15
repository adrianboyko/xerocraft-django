
# Standard

# Third Party
from rest_framework import serializers

# Local
import kmkr.models as models


class ShowSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Show
        fields = (
            'id',
            'title',
            'duration',
            'description',
            'active'
        )


class TrackSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Track
        fields = (
            'id',
            'title',
            'artist',
            'radiodj_id',
            'track_type',
            'duration'
        )


class PlayLogEntrySerializer(serializers.ModelSerializer):

    show = serializers.HyperlinkedRelatedField(read_only=True, view_name='kmkr:show-detail')

    track_embed = TrackSerializer(many=False, read_only=True, source='track')

    class Meta:
        model = models.PlayLogEntry
        fields = (
            'id',
            'track_embed',
            'start',
            'show',
            'show_date'
        )
