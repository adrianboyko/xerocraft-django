
# Standard

# Third Party
from rest_framework import serializers

# Local
import tasks.models as tm
import members.models as mm


class ClaimSerializer(serializers.ModelSerializer):

    claimed_task = serializers.HyperlinkedRelatedField(
        view_name='task:task-detail',
        queryset=tm.Task.objects.all(),
        style={'base_template': 'input.html'},
    )

    claiming_member = serializers.HyperlinkedRelatedField(
        view_name='memb:member-detail',
        queryset=mm.Member.objects.all(),
        style={'base_template': 'input.html'},
    )

    work_set = serializers.HyperlinkedRelatedField(
        view_name='task:work-detail',
        read_only=True,
        many=True,
        style={'base_template': 'input.html'},
    )

    class Meta:
        model = tm.Claim
        fields = (
            'claimed_duration',
            'claimed_start_time',
            'claimed_task',
            'claiming_member',
            'date_verified',
            'id',
            'status',
            'work_set',
        )


class PlaySerializer(serializers.ModelSerializer):

    playing_member = serializers.HyperlinkedRelatedField(
        view_name='memb:member-detail',
        queryset=mm.Member.objects.all(),
        style={'base_template': 'input.html'},
    )

    class Meta:
        model = tm.Play
        fields = (
            'id',
            'play_date',
            'play_duration',
            'play_start_time',
            'playing_member',
        )


class TaskSerializer(serializers.ModelSerializer):

    # TODO: owner, reviewer, etc, should not be read-only.
    owner = serializers.HyperlinkedRelatedField(read_only=True, view_name='memb:member-detail')
    reviewer = serializers.HyperlinkedRelatedField(read_only=True, view_name='memb:member-detail')
    eligible_claimants = serializers.HyperlinkedRelatedField(
        read_only=True, many=True, view_name='memb:member-detail', source='eligible_claimants_2'
    )
    claim_set = ClaimSerializer(many=True, read_only=True)
    name_of_likely_worker = serializers.ReadOnlyField()  # This is a helpful "denormalization"

    # REVIEW: Having both of these seems redundant but both will remain, for now, for compatibility reasons.
    is_fully_claimed = serializers.ReadOnlyField()
    staffing_status = serializers.ReadOnlyField()

    class Meta:
        model = tm.Task
        fields = (
            'anybody_is_eligible',
            'claim_set',
            'creation_date',
            'deadline',
            'eligible_claimants',
            'id',
            'instructions',
            'is_fully_claimed',
            'max_work',
            'max_workers',
            'name_of_likely_worker',
            'owner',
            'priority',
            'reviewer',
            'scheduled_date',
            'short_desc',
            'should_nag',
            'staffing_status',
            'status',
            'work_duration',
            'work_start_time',
        )


class WorkerSerializer(serializers.ModelSerializer):

    member = serializers.HyperlinkedRelatedField(
        view_name='memb:member-detail',
        queryset=tm.Claim.objects.all(),
        style={'base_template': 'input.html'},
    )

    class Meta:
        model = tm.Worker
        fields = (
            'id',
            'member',
            'should_include_alarms',
            'should_nag',
            'should_report_work_mtd',
            'time_acct_balance'
        )


class WorkNoteSerializer(serializers.ModelSerializer):

    work = serializers.HyperlinkedRelatedField(
        view_name='task:work-detail',
        queryset=tm.Work.objects.all(),
        style={'base_template': 'input.html'},
    )

    author = serializers.HyperlinkedRelatedField(
        view_name='memb:member-detail',
        queryset=mm.Member.objects.all(),
        style={'base_template': 'input.html'},
    )

    class Meta:
        model = tm.WorkNote
        fields = (
            'id',
            'author',
            'content',
            'when_written',
            'work',
        )


class WorkSerializer(serializers.ModelSerializer):

    claim = serializers.HyperlinkedRelatedField(
        view_name='task:claim-detail',
        queryset=tm.Claim.objects.all(),
        style={'base_template': 'input.html'},
    )
    witness = serializers.HyperlinkedRelatedField(
        view_name='memb:member-detail',
        queryset=mm.Member.objects.all(),
        allow_null=True,
        style={'base_template': 'input.html'},
    )
    notes = WorkNoteSerializer(many=True, read_only=True)

    class Meta:
        model = tm.Work
        fields = (
            'id',
            'claim',
            'work_date',
            'work_start_time',
            'work_duration',
            'witness',
            'notes',
        )


# ---------------------------------------------------------------------------
# CLASSES
# ---------------------------------------------------------------------------

class ClassxPersonSerializer(serializers.ModelSerializer):

    the_class = serializers.HyperlinkedRelatedField(
        view_name='task:class-detail',
        queryset=tm.Class.objects.all(),
        style={'base_template': 'input.html'},
    )

    the_person = serializers.HyperlinkedRelatedField(
        view_name='memb:member-detail',
        queryset=mm.Member.objects.all(),
        style={'base_template': 'input.html'},
    )

    ro_person_firstname = serializers.CharField(source='person_firstname')
    ro_person_username = serializers.CharField(source='person_username')
    ro_paid = serializers.CharField(source='paid')

    class Meta:
        model = tm.Class_x_Person
        fields = (
            'the_class',
            'the_person',
            'status',
            'status_updated',
            'ro_paid',
            'ro_person_firstname',
            'ro_person_username',
        )


class ClassSerializer(serializers.ModelSerializer):

    teaching_task = serializers.HyperlinkedRelatedField(
        view_name='task:task-detail',
        queryset=tm.Task.objects.all(),
        style={'base_template': 'input.html'},
    )

    persons = ClassxPersonSerializer(
        read_only=True, many=True,
        source='class_x_person_set'
    )

    ro_scheduled_date = serializers.DateField(source='scheduled_date')
    ro_start_time = serializers.TimeField(source='start_time')

    class Meta:
        model = tm.Class
        fields = (
            'id',
            'ro_scheduled_date',
            'ro_start_time',
            'title',
            'short_desc',
            'info',
            'canceled',
            'max_students',
            'department',
            'teaching_task',
            'member_price',
            'nonmember_price',
            'materials_fee',
            'prerequisite_tag',
            'certification_tag',
            'minor_policy',
            'publicity_image',
            'printed_handout',
            'persons',
        )