from django.db import models
from django.utils import timezone
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

    def generate_member_card_str(self):
        # Generate a membership card string which is 32 characters of url-safe base64.
        u1 = uuid.uuid4().bytes
        u2 = uuid.uuid4().bytes
        b64 = base64.urlsafe_b64encode(u1+u2).decode()[:32]
        md5 = hashlib.md5(b64.encode()).hexdigest()

        # Check for md5 hash collision.
        md5_count = Member.objects.filter(membership_card_md5=md5).count()
        assert md5_count <= 1 # Greater than 1 means collision checking has somehow failed in the past.
        if md5_count > 0:
            # Collision detected, so try again.
            return self.generate_member_card_str()

        # Save the the md5 of the base64 string in the member table.
        # Since login is required for this view, User.DoesNotExist will not be thrown.
        self.membership_card_md5 = md5
        self.membership_card_when = timezone.now()
        self.save()
        return b64

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

    def validate(self):
        if self.membership_card_md5 is not None:
            if len(self.membership_card_md5) != self.MEMB_CARD_STR_LEN:
                return False, "Bad membership card string."
            if self.auth_user is None:
                return False, "Every Member must be linked to a User."
        return True, "Looks good"

    def __str__(self):
        return "%s %s" % (self.auth_user.first_name, self.auth_user.last_name)

    # Note: Can't order Member because the interesting fields are in auth.User
    # class Meta:
    #     ordering = ['']


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
