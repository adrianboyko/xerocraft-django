
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


class EpisodeTrackSerializer(serializers.ModelSerializer):

    episode = serializers.HyperlinkedRelatedField(
        view_name='kmkr:episode-detail',
        queryset = models.Episode.objects.all(),
    )

    class Meta:
        model = models.EpisodeTrack
        fields = (
            'id',
            'episode',
            'sequence',
            'artist',
            'title',
            'duration'
        )


class EpisodeSerializer(serializers.ModelSerializer):

    show = serializers.HyperlinkedRelatedField(
        view_name='kmkr:show-detail',
        queryset = models.Show.objects.all()
    )
    tracks_embed = EpisodeTrackSerializer(many=True, read_only=True, source='episodetrack_set')

    class Meta:
        model = models.Episode
        fields = (
            'id',
            'show',
            'first_broadcast',
            'title',
            'tracks_embed'
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

    track_embed = TrackSerializer(many=False, read_only=True, source='track')

    class Meta:
        model = models.PlayLogEntry
        fields = (
            'id',
            'track_embed',
            'start',
        )
