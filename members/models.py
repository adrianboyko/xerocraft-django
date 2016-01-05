from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import base64
import uuid
import hashlib

# TODO: Rework various validate() methods into Model.clean()? See Django's "model validation" docs.

# TODO: class MetaTag?  E.g. Tag instructor tags with "instructor" meta-tag?

# TODO: Import various *Field classes and remove "models."?


# class MetaTag(models.Model):
#
#     name = models.CharField(max_length=40,
#         help_text="A short name for the metatag.")
#     meaning = models.TextField(max_length=500,
#         help_text="A discussion of the metatag's semantics. What does it mean? What does it NOT mean?")
#
#     def __str__(self):
#         return self.name

class Tag(models.Model):
    """ A tag represents some attribute of a Member. Examples are various skills, shop roles, or shop permissions.
    """
    name = models.CharField(max_length=40, unique=True,
        help_text="A short name for the tag.")
    meaning = models.TextField(max_length=500,
        help_text="A discussion of the tag's semantics. What does it mean? What does it NOT mean?")
    # meta_tags = models.ManyToManyField(MetaTag, blank=True,
    #     help_text="A tag can have zero or more metatags.")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Member(models.Model):
    """Represents a Xerocraft member.
    Member is an extension of auth.User that adds Xerocraft-specific state like "tags".
    """
    MEMB_CARD_STR_LEN = 32

    auth_user = models.OneToOneField('auth.User', null=False, unique=True, related_name="member",
        help_text="This must point to the corresponding auth.User object.")

    # Saving as MD5 provides some protection against read-only attacks.
    membership_card_md5 = models.CharField(max_length=MEMB_CARD_STR_LEN, null=True, blank=True,
        help_text="MD5 checksum of the random urlsafe base64 string on the membership card.")

    membership_card_when = models.DateTimeField(null=True, blank=True,
        help_text="Date/time on which the membership card was created.")

    tags = models.ManyToManyField(Tag, blank=True, related_name="members",
        through='Tagging', through_fields=('tagged_member', 'tag'))

    @staticmethod
    def generate_auth_token_str(is_unique):
        """Generate a token (and its md5) which will be used in nag email urls, icalendar urls, etc."""

        # Note: This is very similar to the generator in membership. Should there be one util that serves both apps?

        # Generate a token which is 32 characters of url-safe base64.
        u1 = uuid.uuid4().bytes
        u2 = uuid.uuid4().bytes
        b64 = base64.urlsafe_b64encode(u1+u2).decode()[:32]

        # Calculate md5 of the b64 and start over if there's a md5 collision
        md5 = hashlib.md5(b64.encode()).hexdigest()
        if is_unique(md5):
            return b64,md5
        else:
            # Collision detected, so try again.
            return Member.generate_auth_token_str(is_unique)

    def generate_member_card_str(self):

        def unique(token: str) -> bool:
            md5_count = Member.objects.filter(membership_card_md5=token).count()
            assert md5_count <= 1 # Greater than 1 means collision checking has somehow failed in the past.
            return md5_count == 0

        b64,md5 = Member.generate_auth_token_str(unique)
        # Save the the md5 of the base64 string in the member table.
        self.membership_card_md5 = md5
        self.membership_card_when = timezone.now()
        self.save()
        return b64

    def is_tagged_with(self, tag_name):
        return True if tag_name in [x.name for x in self.tags.all()] else False

    def can_tag_with(self, tag):
        for tagging in self.taggings.all():
            if tagging.tag.name == tag.name:
                return tagging.can_tag
        return False

    def is_domain_staff(self):
        return self.is_tagged_with("Staff")

    @property
    def first_name(self): return self.auth_user.first_name

    @property
    def last_name(self): return self.auth_user.last_name

    @property
    def username(self): return self.auth_user.username

    @property
    def email(self): return self.auth_user.email

    @property
    def is_active(self): return self.auth_user.is_active

    @staticmethod
    def get_by_card_str(member_card_str):
        member_card_md5 = hashlib.md5(member_card_str.encode()).hexdigest()
        try:
            return Member.objects.get(membership_card_md5=member_card_md5)
        except Member.DoesNotExist:
            return None

    @staticmethod
    def get_for_staff(member_card_str, staff_card_str):
        """ Given a member card string and a staff card string, return details for the member.
            Returns (True, (member, staff)) on success
            Returns (False, error_message) on failure
        """

        # Look up the subject member and the staff member and report various possible errors:
        member = Member.get_by_card_str(member_card_str)
        if member is None: return False, "Invalid member card"
        staff = Member.get_by_card_str(staff_card_str)
        if staff is None: return False, "Invalid staff card"
        if not staff.is_domain_staff(): return False, "Not a staff member"
        return True, (member, staff)

    # TODO: Add case-insensitive index to User.username for performance.
    # TODO: Add code somewhere to ensure that email addresses for users are unique.
    @staticmethod
    def get_local_user(identifier):
        # NOTE! In code below, "identifier" means "username or email address".
        if identifier is None:
            return None
        if identifier.isspace() or len(identifier) == 0:
            return None
        try:
            user = User.objects.get(username__iexact=identifier)
            return user
        except User.DoesNotExist:
            pass
        try:
            user = User.objects.get(email__iexact=identifier)
            return user
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_local_member(identifier):
        user = Member.get_local_user(identifier)
        if user is not None: return user.member
        return None

    def validate(self):
        if self.membership_card_md5 is not None:
            if len(self.membership_card_md5) != self.MEMB_CARD_STR_LEN:
                return False, "Bad membership card string."
            if self.auth_user is None:
                return False, "Every Member must be linked to a User."
        return True, "Looks good"

    def __str__(self):
        if self.first_name != "" and self.last_name != "":
            return "%s %s" % (self.first_name, self.last_name)
        else:
            return self.username

    class Meta:
        ordering = ['auth_user__first_name','auth_user__last_name']


class Tagging(models.Model):
    """ Intermediate table representing the many-tomany relation between Member and Tag
    """
    tagged_member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='taggings',
        help_text="The member tagged.")

    date_tagged = models.DateTimeField(null=False, blank=False, auto_now_add=True,
        help_text="Date/time on which the member was tagged.")

    tag = models.ForeignKey(Tag, on_delete=models.CASCADE,
        help_text="The tag assigned to the member.")

    authorizing_member = models.ForeignKey(Member, null=True, blank=False, on_delete=models.SET_NULL, related_name='authorized_taggings',
        help_text="The member that authorized that the member be tagged.")
        # Note: If authorizing member is deleted, his/her Taggings shouldn't be. Hence on_delete=SET_NULL.
        # However, blank=False because somebody using admin really should provide the authorizing member info.

    can_tag = models.BooleanField(default=False,
        help_text="If True, the tagged member can be a authorizing member for this tag.")
        # Note: Above assumes that only people with a certain tag can grant that tag.
        # However, Django admins with appropriate permissions can tag any member with any tag, when required.

    @staticmethod
    def add_if_permitted(tagger, taggee, tag):
        if taggee.is_tagged_with(tag.name): return
        if tagger.can_tag_with(tag):
            Tagging.objects.create(tagged_member=taggee, tag=tag, authorizing_member=tagger)

    @staticmethod
    def remove_if_permitted(tagger, taggee, tag):
        if not taggee.is_tagged_with(tag.name): return
        if tagger.can_tag_with(tag):
            try:
                tag = Tagging.objects.get(tagged_member=taggee, tag=tag)
                tag.delete()
            except Tagging.DoesNotExist:
                pass

    def __str__(self):
        return "%s/%s/%s" % (self.tagged_member.auth_user.username, self.tag.name, self.can_tag)

    class Meta:
        unique_together = ('tagged_member', 'tag')


class MemberNote(models.Model):

    # Note will become anonymous if author is deleted or author is blank.
    author = models.ForeignKey(Member, null=True, blank=True, on_delete=models.SET_NULL, related_name="member_notes_authored",
        help_text="The member who wrote this note.")
    content = models.TextField(max_length=2048,
        help_text="For staff. Anything you want to say about the member.")
    task = models.ForeignKey(Member, on_delete=models.CASCADE)


class VisitEvent(models.Model):

    who = models.ForeignKey(Member, on_delete=models.PROTECT,
        help_text="The member who's visiting or visited.")

    when = models.DateTimeField(null=False, blank=False, auto_now_add=True,
        help_text="Date/time of visit event.")

    METHOD_RFID = "R"
    METHOD_FRONT_DESK = "F"
    METHOD_MOBILE_APP = "M"
    METHOD_UNKNOWN = "U"
    VISIT_METHOD_CHOICES = [
        (METHOD_RFID, "RFID"),
        (METHOD_FRONT_DESK, "Front Desk"),
        (METHOD_MOBILE_APP, "Mobile App"),
        (METHOD_UNKNOWN, "Unknown"),
    ]
    method = models.CharField(max_length=1, choices=VISIT_METHOD_CHOICES,
        default=METHOD_UNKNOWN, null=False, blank=False,
        help_text="The method used to record the visit, such as 'Front Desk' or 'RFID'.")

    EVT_ARRIVAL = "A"
    EVT_PRESENT = "P"
    EVT_DEPARTURE = "D"
    VISIT_EVENT_CHOICES = [
        (EVT_ARRIVAL, "Arrival"),
        (EVT_PRESENT, "Presence"),
        (EVT_DEPARTURE, "Departure")
    ]
    event_type = models.CharField(max_length=1, choices=VISIT_EVENT_CHOICES, null=False, blank=False,
        help_text="The type of visit event.")

    sync1 = models.BooleanField(default=False,
        help_text="True if this event has been sync'ed to 'other system #1'")

    def __str__(self):
        return "%s, %s %s, %s" % (self.when.isoformat()[:10], self.who.first_name, self.who.last_name, self.event_type)

    class Meta:
        ordering = ['when']

"""
class MembershipPayment(models.Model):

    membership_type

    payment_processor

    amount_paid = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The full amount paid by the member, including payment processing fee, if any.")

    fee_deducted = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The fee deducted from 'amount paid' by the payment processor, if any.")

    family_count = models.IntegerField(default=0, null=False, blank=False,
        help_text="The number of ADDITIONAL family members included in this membership. Usually zero.")

    payment_date = models.DateField(null=True, blank=True,
        help_text="The date on which the payment was made.")

    start_date = models.DateField(null=False, blank=False,
        help_text="The frist day on which the membership is valid.")

    end_date = models.DateField(null=False, blank=False,
        help_text="The last day on which the membership is valid.")

    note = models.TextField(max_length=2048,
        help_text="For staff. Anything you want to say about this payment or membership.")
"""