
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


class ManualPlayListEntrySerializer(serializers.ModelSerializer):

    live_show_instance = serializers.HyperlinkedRelatedField(read_only=True, view_name='kmkr:showinstance-detail')

    class Meta:
        model = models.ManualPlayListEntry
        fields = (
            'live_show_instance',
            'sequence',
            'artist',
            'title',
            'duration'
        )


class ShowInstanceSerializer(serializers.ModelSerializer):

    show = serializers.HyperlinkedRelatedField(read_only=True, view_name='kmkr:show-detail')
    playlist_embed = ManualPlayListEntrySerializer(many=True, read_only=True, source='manualplaylistentry_set')

    class Meta:
        model = models.ShowInstance
        fields = (
            'show',
            'date',
            'host_checked_in',
            'repeat_of',
            'playlist_embed'
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
