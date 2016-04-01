from django.db import models
from django.db.migrations.recorder import MigrationRecorder
from django.utils import timezone
from django.contrib.auth.models import User
from books.models import Sale, ExpenseClaim
import base64
import uuid
import hashlib
from nameparser import HumanName
from datetime import datetime, date, timedelta
from decimal import Decimal

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# CTRLID Functions
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

# REVIEW: There is a nonzero probability that default ctrlids will collide when two users are doing manual data
# entry at the same time.  This isn't considered a significant problem since we'll be lucky to get ONE person to
# do data entry. If it does become a problem, the probability could be reduced by using random numbers.

GEN_CTRLID_PFX = "GEN:"  # The prefix for generated ctrlids.


def next_payment_ctrlid():
    raise NotImplementedError("This method is referenced by 0025_auto_20160215_1529.py but shouldn't be called.")


def next_membership_ctrlid():

    """Provides an arbitrary default value for the ctrlid field, necessary when data is being entered manually."""

    # This method can't calc a ctrlid before ctrlid col is in db, i.e. before migration 0042.
    # Returning an arbitrary string guards against failure during creation of new database, e.g. during tests.
    migs = MigrationRecorder.Migration.objects.filter(app='members', name="0042_auto_20160303_1717")
    if len(migs) == 0: return "arbitrarystring"

    try:
        latest_mship = Membership.objects.filter(ctrlid__startswith=GEN_CTRLID_PFX).latest('ctrlid')
        latest_ctrlid_num = int(latest_mship.ctrlid.replace(GEN_CTRLID_PFX,""))
        return GEN_CTRLID_PFX+str(latest_ctrlid_num+1).zfill(6)
    except Membership.DoesNotExist:
        # This only happens for a new database when there are no physical paid memberships.
        return GEN_CTRLID_PFX+("0".zfill(6))


def next_giftcardref_ctrlid():

    """Provides an arbitrary default value for the ctrlid field, necessary when data is being entered manually."""

    # This method can't refer to MGCR before the new cols are in db. I.e. before migration 0043.
    # Shorting out guards against failure during creation of new database, e.g. during tests.
    migs = MigrationRecorder.Migration.objects.filter(app='members', name="0043_auto_20160309_1455")
    if len(migs) == 0: return

    try:
        # NOTE: This version uses prev created PKs instead of prev created ctrlids.
        # This elminates the need for complicated three-part migrations and MigrationRecorder checks.
        # This may have problems if PKs are reused but they're not in Django + PostgreSQL.
        latest_gcr = MembershipGiftCardReference.objects.latest('id')
        return GEN_CTRLID_PFX+str(int(latest_gcr.id)+1).zfill(6)
    except MembershipGiftCardReference.DoesNotExist:
        # This only happens for a new database when there are no physical paid memberships.
        return GEN_CTRLID_PFX+("0".zfill(6))


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Models
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

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

    def is_domain_staff(self):  # Different than website staff.
        return self.is_tagged_with("Staff")

    def is_currently_paid(self, grace_period=timedelta(0)):
        ''' Determine whether member is currently covered by a membership with a given grace period.'''
        now = datetime.now().date()

        # pm = PaidMembership.objects.filter(
        #     member=self,
        #     start_date__lte=now, end_date__gte=now-grace_period)
        # if len(pm) > 0:
        #     return True

        m = Membership.objects.filter(
            member=self,
            start_date__lte=now, end_date__gte=now-grace_period)
        if len(m) > 0:
            return True

        return False

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
    tagged_member = models.ForeignKey(Member, related_name='taggings',
        on_delete=models.CASCADE,  # If a member is deleted, it doesn't make sense to keep their taggings.
        help_text="The member tagged.")

    date_tagged = models.DateTimeField(null=False, blank=False, auto_now_add=True,
        help_text="Date/time on which the member was tagged.")

    tag = models.ForeignKey(Tag,
        on_delete=models.CASCADE,  # If a tag is deleted, it doesn't make sense to keep the associated taggings.
        help_text="The tag assigned to the member.")

    authorizing_member = models.ForeignKey(Member, null=True, blank=False, related_name='authorized_taggings',
        on_delete=models.SET_NULL,  # If the member who created the tagging is deleted, the tagging should remain.
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

    # Note will be anonymous if author is deleted or author is blank.
    author = models.ForeignKey(Member, null=True, blank=True, related_name="member_notes_authored",
        on_delete=models.SET_NULL,  # If the person who wrote the note is deleted, the note should be kept.
        help_text="The member who wrote this note.")

    content = models.TextField(max_length=2048,
        help_text="For staff. Anything you want to say about the member.")

    member = models.ForeignKey(Member,
        on_delete=models.CASCADE,  # If a member is deleted, any notes concerning them should be deleted.
        help_text="The member to which this note pertains.")


class VisitEvent(models.Model):

    who = models.ForeignKey(Member,
        on_delete=models.PROTECT,  # Visit info is too valuable to be deleted or detached from member info.
        help_text="The member who's visiting or visited.")

    when = models.DateTimeField(null=False, blank=False, default=timezone.now,
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
        return "%s, %s, %s" % (self.when.isoformat()[:10], self.who, self.event_type)

    class Meta:
        ordering = ['when']
        unique_together = ('who', 'when')


class MemberLogin(models.Model):
    """ Record member, datetime, ip for each login. """

    member = models.ForeignKey(Member,
        null=True, blank=True,  # Might log IPs for unauthenticated users.
        on_delete=models.SET_NULL,  # Keep login even if member is deleted, since IP info could be useful.
        help_text="The member who logged in.")

    when = models.DateTimeField(null=False, blank=False, default=timezone.now,
        help_text="Date/time member logged in.")

    ip = models.GenericIPAddressField(null=False, blank=False,
        help_text="IP address from which member logged in.")

    class Meta:
        verbose_name="Login"


def next_paidmembership_ctrlid():
    '''Provides an arbitrary default value for the ctrlid field, necessary when check, cash, or gift-card data is being entered manually.'''
    # REVIEW: There is a nonzero probability that default ctrlids will collide when two users are doing manual data entry at the same time.
    #         This isn't considered a significant problem since we'll be lucky to get ONE person to do data entry.
    #         If it does become a problem, the probability could be reduced by using random numbers.
    physical_pay_methods = [
        PaidMembership.PAID_BY_NA,  # This is the "physical" payment method in the case of complimentary memberships.
        PaidMembership.PAID_BY_CASH,
        PaidMembership.PAID_BY_CHECK,
        PaidMembership.PAID_BY_GIFT,
    ]
    physical_count = PaidMembership.objects.filter(payment_method__in=physical_pay_methods).count()
    if physical_count > 0:
        latest_pm = PaidMembership.objects.filter(payment_method__in=physical_pay_methods).latest('ctrlid')
        return str(int(latest_pm.ctrlid)+1).zfill(6)
    else:
        # This only happens for a new database when there are no physical paid memberships.
        return "0".zfill(6)


class GroupMembership(models.Model):

    group_tag = models.ForeignKey(Tag, null=False, blank=False,
        on_delete=models.PROTECT,  # A group membership's tag should be changed before deleting the unwanted tag.
        help_text="The group to which this membership applies, defined by a tag.")

    start_date = models.DateField(null=False, blank=False,
        help_text="The first day on which the membership is valid.")

    end_date = models.DateField(null=False, blank=False,
        help_text="The last day on which the membership is valid.")

    max_members = models.IntegerField(default=None, null=True, blank=True,
        help_text="The maximum number of members to which this group membership can be applied. Blank if no limit.")

    # A membership can be sold. Sale related fields: sale, sale_price

    sale = models.ForeignKey(Sale, null=False, blank=False,
        on_delete=models.CASCADE,  # Line items are parts of the sale so they should be deleted.
        help_text="The sale on which this group membership appears as a line item, if any.")

    sale_price = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The price at which this item sold.")

    def __str__(self):
        return "{}, {} to {}".format(self.group_tag, self.start_date, self.end_date)

    def matches(self, membership):
        if membership.start_date      != self.start_date: return False
        if membership.end_date        != self.end_date: return False
        if membership.membership_type != membership.MT_GROUP: return False
        return True

    def copy_to(self, membership):
        membership.start_date      = self.start_date
        membership.end_date        = self.end_date
        membership.membership_type = Membership.MT_GROUP
        membership.save()

    def get_or_create_membership_for(self, member):
        """Get or create a membership and ensure that it matches the group membership's parameters."""

        defaults = {
            'start_date':      self.start_date,
            'end_date':        self.end_date,
            'membership_type': Membership.MT_GROUP
        }
        membership, created = Membership.objects.get_or_create(member=member, group=self, defaults=defaults)
        if created or not self.matches(membership): self.copy_to(membership)
        return membership

    def sync_memberships(self):
        # Create or update the membership for each person in the group:
        for member in self.group_tag.members.all():
            # Following ensures that the membership is synched
            self.get_or_create_membership_for(member)
        # Deletion of memberships for people who are no longer in the group will be handled in
            # a signal handler for Tagging deletions.


class PaidMembership(models.Model):

    member = models.ForeignKey(Member, related_name='terms',
        # There are records of payments which no longer seem to have an associated account.
        # Name used when paying may be different enough to prevent auto-linking.
        # For two reasons listed above, we allow nulls in next line.
        default=None, null=True, blank=True,
        on_delete=models.PROTECT,  # Don't delete payment info nor the member linked to it.
        help_text="The member to whom this paid membership applies.")

    # Note: Strictly speaking, memberships have types, and members don't.
    # Note: If there's no membership term covering some period, member has an "unpaid" membership during that time.
    # REVIEW: Should Scholarship collapse into Complimentary?
    MT_REGULAR       = "R"  # E.g. members who pay $50/mo
    MT_WORKTRADE     = "W"  # E.g. members who work 9 hrs/mo and pay reduced $10/mo
    MT_SCHOLARSHIP   = "S"  # The so-called "full scholarship", i.e. $0/mo. These function as paid memberships.
    MT_COMPLIMENTARY = "C"  # E.g. for directors, certain sponsors, etc. These function as paid memberships.
    MT_GROUP         = "G"  # E.g. for directors, certain sponsors, etc. These function as paid memberships.
    MEMBERSHIP_TYPE_CHOICES = [
        (MT_REGULAR,       "Regular"),
        (MT_WORKTRADE,     "Work-Trade"),
        (MT_SCHOLARSHIP,   "Scholarship"),
        (MT_COMPLIMENTARY, "Complimentary"),
        (MT_GROUP,         "Group"),
    ]
    membership_type = models.CharField(max_length=1, choices=MEMBERSHIP_TYPE_CHOICES,
        null=False, blank=False, default=MT_REGULAR,
        help_text="The type of membership.")

    family_count = models.IntegerField(default=0, null=False, blank=False,
        help_text="The number of ADDITIONAL family members included in this membership. Usually zero.")

    start_date = models.DateField(null=False, blank=False,
        help_text="The first day on which the membership is valid.")

    end_date = models.DateField(null=False, blank=False,
        help_text="The last day on which the membership is valid.")

    payer_name = models.CharField(max_length=40, blank=True,
        help_text="Name of person who made the payment.")

    payer_email = models.EmailField(max_length=40, blank=True,
        help_text="Email address of person who made the payment.")

    payer_notes = models.CharField(max_length=1024, blank=True,
        help_text="Any notes provided by the member.")

    PAID_BY_NA     = "0"
    PAID_BY_CASH   = "$"
    PAID_BY_CHECK  = "C"
    PAID_BY_GIFT   = "G"
    PAID_BY_SQUARE = "S"
    PAID_BY_2CO    = "2"
    PAID_BY_WEPAY  = "W"
    PAID_BY_PAYPAL = "P"
    PAID_BY_CHOICES = [
        (PAID_BY_NA,     "N/A"),  # E.g. complimentary "paid" memberships have no payment method.
        (PAID_BY_CASH,   "Cash"),
        (PAID_BY_CHECK,  "Check"),
        (PAID_BY_GIFT,   "Gift Card"),  # These entries are made when person redeems the gift card.
        (PAID_BY_SQUARE, "Square"),
        (PAID_BY_2CO,    "2Checkout"),
        (PAID_BY_WEPAY,  "WePay"),
        (PAID_BY_PAYPAL, "PayPal"),
    ]
    payment_method = models.CharField(max_length=1, choices=PAID_BY_CHOICES,
        null=False, blank=False, default=PAID_BY_CASH,
        help_text="The payment method used.")

    paid_by_member = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The full amount paid by the member, including payment processing fee IF THEY PAID IT.")
    paid_by_member.verbose_name = "Amt Paid by Member"

    processing_fee = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="Payment processor's fee, regardless of whether it was paid by the member or Xerocraft.")
    processing_fee.verbose_name = "Amt of Processing Fee"

    ctrlid = models.CharField(max_length=40, null=False, blank=False, default=next_paidmembership_ctrlid,
        help_text="Payment processor's id for this payment.")

    payment_date = models.DateField(null=True, blank=True,
        help_text="The date on which the payment was made. Can be blank if unknown.")

    protected = models.BooleanField(default=False,
        help_text="Protect against further auto processing by ETL, etc. Prevents overwrites of manually enetered data.")

    def link_to_member(self):

        self.member = None

        # Attempt to match by EMAIL
        try:
            email_matches = User.objects.filter(email=self.payer_email)
            if len(email_matches) == 1:
                self.member = email_matches[0].member
        except User.DoesNotExist:
            pass

        # Attempt to match by NAME
        nameobj = HumanName(self.payer_name)
        fname = nameobj.first
        lname = nameobj.last
        try:
            name_matches = User.objects.filter(first_name__iexact=fname, last_name__iexact=lname)
            if len(name_matches) == 1:
                self.member = name_matches[0].member
            # TODO: Else log WARNING (or maybe just INFO)
        except User.DoesNotExist:
            pass

    def __str__(self):
        return "%s, %s, %s" % (self.member, self.start_date, self.end_date)

    class Meta:
        unique_together = ('payment_method', 'ctrlid')


class PaidMembershipNudge(models.Model):
    """ Records the fact that we reminded somebody that they should renew their paid membership """

    member = models.ForeignKey(Member, null=False, blank=False,
        on_delete=models.CASCADE,  # If a member is deleted, we don't care that we've nudged him to pay.
        help_text="The member we reminded.")

    when = models.DateField(null=False, blank=False, default=timezone.now,
        help_text="Date on which the member was reminded.")

    class Meta:
        verbose_name="Renewal reminder"


class MembershipGiftCard(models.Model):

    redemption_code = models.CharField(max_length=20, unique=True, null=False, blank=False,
        help_text="A random string printed on the card, used during card redemption / membership activation.")

    date_created = models.DateField(null=False, blank=False, default=timezone.now,
        help_text="The date on which the gift card was created.")

    price = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The price to buy this gift card.")

    month_duration = models.IntegerField(null=False, blank=False,
        help_text="The number of months of membership this gift card grants when redeemed.")

    def __str__(self):
        return "{} months for ${}, code: {}".format(self.month_duration, self.price, self.redemption_code)

    class Meta:
        verbose_name="Gift card"


class MembershipGiftCardRedemption(models.Model):

    redemption_date = models.DateField(null=False, blank=False, default=timezone.now,
        help_text="The date on which the gift card was redeemed.")

    card = models.OneToOneField(MembershipGiftCard, null=False, blank=False,
        on_delete=models.PROTECT,  # It's nonsensical to delete a gift card after it's redeemed.
        help_text="The membership gift card that was redeemed.")

    def __str__(self):
        return "{}, code: {}".format(
            str(self.membership_set.first()),
            self.card.redemption_code
        )

    class Meta:
        verbose_name="Gift card redemption"


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# MEMBERSHIP
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

# Along with Sale (in "books" app), the following class will eventually replace PaidMembership.
# PaidMembership is being kept until the switch-over is complete.

class Membership(models.Model):

    # A membership can arise from redemption of a gift card.
    redemption = models.ForeignKey(MembershipGiftCardRedemption, null=True, blank=True, default=None,
        on_delete=models.CASCADE,  # If the redemption is deleted, this membership is meaningless.
        help_text="The associated membership gift card redemption, if any. Usually none.")

    # A membership can be part of a group membership
    group = models.ForeignKey(GroupMembership, null=True, blank=True, default=None,
        on_delete=models.CASCADE,  # This membership is part of the group membership, so it should also go.
        help_text="The associated group membership, if any. Usually none.")

    member = models.ForeignKey(Member,
        # There are records of payments which no longer seem to have an associated account.
        # Name used when paying may be different enough to prevent auto-linking.
        # For two reasons listed above, we allow nulls in next line.
        default=None, null=True, blank=True,
        on_delete=models.SET_NULL,  # If the member is deleted, this membership info is still useful for stats.
        help_text="The member to whom this membership applies.")

    # Note: Strictly speaking, memberships have types, and members don't.
    # Note: If there's no membership term covering some period, member has an "unpaid" membership during that time.
    # REVIEW: Should Scholarship collapse into Complimentary?
    MT_REGULAR       = "R"  # E.g. members who pay $50/mo
    MT_WORKTRADE     = "W"  # E.g. members who work 9 hrs/mo and pay reduced $10/mo
    MT_SCHOLARSHIP   = "S"  # The so-called "full scholarship", i.e. $0/mo. These function as paid memberships.
    MT_COMPLIMENTARY = "C"  # E.g. for directors, certain sponsors, etc. These function as paid memberships.
    MT_GROUP         = "G"  # E.g. Bit Buckets, Pima Engineering Club, JobPath
    MT_FAMILY        = "F"  # An add-on family membership associated with a regular or work-trade membership.
    MEMBERSHIP_TYPE_CHOICES = [
        (MT_REGULAR,       "Regular"),
        (MT_WORKTRADE,     "Work-Trade"),
        (MT_SCHOLARSHIP,   "Scholarship"),
        (MT_COMPLIMENTARY, "Complimentary"),
        (MT_GROUP,         "Group"),
        (MT_FAMILY,        "Family"),
    ]
    membership_type = models.CharField(max_length=1, choices=MEMBERSHIP_TYPE_CHOICES,
        null=False, blank=False, default=MT_REGULAR,
        help_text="The type of membership.")

    start_date = models.DateField(null=False, blank=False, default=date.today,
        help_text="The first day on which the membership is valid.")

    end_date = models.DateField(null=False, blank=False, default=date.today,
        help_text="The last day on which the membership is valid.")

    # A membership can be sold. Sale related fields: sale, sale_price

    sale = models.ForeignKey(Sale, null=True, blank=True, default=None,
        on_delete=models.CASCADE,  # Line items are parts of the sale so they should be deleted.
        help_text="The sale that includes this line item, if any. E.g. comp memberships don't have a corresponding sale.")

    sale_price = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        # In the gift-card redemption context I don't want to confuse admin users by requiring them to provide
        # a sale price of $0. So I'll let this default to zero even though it must be non-zero in other contexts.
        default=Decimal(0.0),
        help_text="The price at which this item sold.")

    # ETL related fields: ctrlid, protected

    ctrlid = models.CharField(max_length=40, null=False, blank=False, unique=True,
        default=next_membership_ctrlid,
        help_text="Payment processor's id for this membership if it was part of an online purchase.")

    protected = models.BooleanField(default=False,
        help_text="Protect against further auto processing by ETL, etc. Prevents overwrites of manually entered data.")

    def link_to_member(self):

        if self.sale is None:
            return

        # If payer's acct was specified in sale, link to it.
        if self.sale.payer_acct is not None:
            self.member = self.sale.payer_acct.member
            return

        # Attempt to match by EMAIL
        try:
            email_matches = User.objects.filter(email=self.sale.payer_email)
            if len(email_matches) == 1:
                self.member = email_matches[0].member
                return
        except User.DoesNotExist:
            pass

        # Attempt to match by NAME
        nameobj = HumanName(self.sale.payer_name)
        fname = nameobj.first
        lname = nameobj.last
        try:
            name_matches = User.objects.filter(first_name__iexact=fname, last_name__iexact=lname)
            if len(name_matches) == 1:
                self.member = name_matches[0].member
                return
            else:
                pass  # TODO: Log WARNING (or maybe just INFO)
        except User.DoesNotExist:
            pass

    def __str__(self):
        return "%s, %s to %s" % (self.member, self.start_date, self.end_date)


class DiscoveryMethod(models.Model):
    """Different ways that members learn about us. E.g. 'Tucson Meet Yourself', 'Radio', 'TV', 'Website', etc """

    name = models.CharField(max_length=30, unique=True, null=False, blank=False,
        help_text="The name of some means by which people learn about our organization.")

    order = models.IntegerField(default=None, unique=True, null=False, blank=False,
        help_text="These values define the order in which the discovery methods should be presented to users.")


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Additional Line-Item Models for SaleAdmin in Books app.
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

# NOTE: Making MembershipGiftCard a LineItem results in user needing to create the card info at time of sale.
# Adding this MembershipGiftCardReference class lets the user select an existing MembershipGiftCard instead.

class MembershipGiftCardReference(models.Model):

    # NOTE: Cards have been sold online without any info about which card was sold.
    # That situation will be mapped to a card value of None and should be rectified manually.
    card = models.OneToOneField(MembershipGiftCard, null=True, blank=True,
        on_delete=models.PROTECT,  # It doesn't make sense to delete a gift card if it's sold.
        help_text="The membership gift card being sold.")

    # Membership gift cards can be sold. Sales related fields: sale, sale_price

    sale = models.ForeignKey(Sale, null=True, blank=True,
        on_delete=models.CASCADE,  # Line items are parts of the sale so they should be deleted.
        help_text="The sale that includes the card as a line item.")

    sale_price = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        help_text="The price at which this item sold.")

    # ETL related fields: ctrlid, protected

    ctrlid = models.CharField(max_length=40, null=False, blank=False, unique=True,
        default=next_giftcardref_ctrlid,
        help_text="Payment processor's id if this was part of an online purchase.")

    protected = models.BooleanField(default=False,
        help_text="Protect against further auto processing by ETL, etc. Prevents overwrites of manually entered data.")

    def __str__(self):
        return "CARD NOT YET SPECIFIED!" if self.card is None else self.card.redemption_code

    class Meta:
        verbose_name = "Membership gift card"
