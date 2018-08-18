
# Standard

# Third Party
from rest_framework import serializers

# Local
import kmkr.models as models


class BroadcastSerializer(serializers.ModelSerializer):

    episode = serializers.HyperlinkedRelatedField(
        view_name='kmkr:episode-detail',
        queryset = models.Episode.objects.all()
    )

    class Meta:
        model = models.Broadcast
        fields = (
            'id',
            'episode',
            'date',
            'host_checked_in',
            'type'
        )


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


# These are tracks that were played on-air, e.g. according to RadioDJ.
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

    library_track_embed = TrackSerializer(
        many=False, read_only=True, source='track'
    )

    non_library_track_embed = EpisodeTrackSerializer(
        many=False, read_only=True, source='non_library_track'
    )

    library_track = serializers.HyperlinkedRelatedField(
        view_name='kmkr:track-detail',
        queryset=models.Track.objects.all(),
        source='track',
        required=False,
        allow_null=True
    )

    non_library_track = serializers.HyperlinkedRelatedField(
        view_name='kmkr:episodetrack-detail',
        queryset=models.EpisodeTrack.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = models.PlayLogEntry
        fields = (
            'id',
            'library_track',
            'non_library_track',
            'library_track_embed',
            'non_library_track_embed',
            'start',
        )
