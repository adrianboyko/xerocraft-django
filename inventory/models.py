# pylint: disable=C0330

# Standard
from pytz import timezone

# Third Party
from django.db import models

# Local
from members.models import Member


class Location(models.Model):

    x = models.FloatField(null=True, blank=True,
        help_text="An ordinate in some coordinate system to help locate the location.")

    y = models.FloatField(null=True, blank=True,
        help_text="An ordinate in some coordinate system to help locate the location.")

    z = models.FloatField(null=True, blank=True,
        help_text="An ordinate in some coordinate system to help locate the location.")

    short_desc = models.CharField(max_length=40, null=True, blank=True,
        help_text="A short description/name for the location.")

    def __str__(self):
        sd = self.short_desc if self.short_desc is not None else "For future use."
        return "L%04d, %s" % (self.pk, sd)

    class Meta:
        ordering = ['pk']


class Shop(models.Model):

    name = models.CharField(max_length=40, blank=False,
        help_text="The name of the shop.")

    manager = models.ForeignKey(Member, null=True, blank=True, related_name='shops_managed',
        on_delete=models.SET_NULL,
        help_text="The member that manages the shop.")

    backup_manager = models.ForeignKey(Member, null=True, blank=True, related_name='shops_backed',
        on_delete=models.SET_NULL,
        help_text="The member that can carry out manager duties when the manager is not available.")

    info_link = models.URLField(null=True, blank=True,
        help_text="A link to some web-based info about the shop, e.g. a Wiki page.")

    def __str__(self):
        return self.name


class Tool(models.Model):
    """Represents a tool, machine, etc. Not consumable."""

    name = models.CharField(max_length=40, blank=False,
        help_text="The resource's name or a short description.")

    shop = models.ForeignKey(Shop, null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="The shop that owns or stocks the resource.")

    location = models.ForeignKey(Location, null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="The location of the resource.")

    def __str__(self):
        toolname = self.name if self.name != "" else "?"
        shopname = self.shop.name if self.shop is not None and self.shop.name != "" else "?"
        return "{} in {}".format(toolname, shopname)


class ToolIssue(models.Model):

    tool = models.ForeignKey(Tool, null=False, blank=False,
        on_delete=models.CASCADE,
        help_text="The member that reported the issue.")

    reporter = models.ForeignKey(Member, null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="The member that reported the issue.")

    short_desc = models.CharField(max_length=40, blank=False,
        help_text="A short description of the issue. In depth description can go in a note.")

    IT_NEW       = "N"  # The issue has been entered but no further action has been taken.
    IT_VALIDATED = "V"  # The issue has been validated by the shop manager.
    IT_CLOSED    = "C"  # The issue has been closed (either dealt with or rejected)
    ISSUE_TYPE_CHOICES = [
        (IT_NEW,       "New Issue"),
        (IT_VALIDATED, "Validated"),
        (IT_CLOSED,    "Closed"),
    ]
    status = models.CharField(max_length=1, choices=ISSUE_TYPE_CHOICES)


class ToolIssueNote(models.Model):

    toolIssue = models.ForeignKey(ToolIssue, null=False, blank=False,
        on_delete=models.CASCADE,
        help_text="Any kind of note about the tool issue.")

    # Note will become anonymous if author is deleted or author is blank.
    author = models.ForeignKey(Member, null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="The member who wrote this note.")

    when_written = models.DateTimeField(null=False, auto_now_add=True,
        help_text="The date and time when the note was written.")

    content = models.TextField(max_length=2048,
        help_text="Anything you want to say about the tool issue.")


class ParkingPermit(models.Model):

    owner = models.ForeignKey(Member, null=False, blank=False, on_delete=models.PROTECT,
        related_name="permits_owned",
        help_text="The member who owns the parked item.")

    created = models.DateField(null=False, blank=False, auto_now_add=True,
        help_text="Date/time on which the parking permit was created.")

    short_desc = models.CharField(max_length=40, blank=False,
        help_text="A short description of the item parked.")

    ok_to_move = models.BooleanField(default=True,
        help_text="Is it OK to carefully move the item to another location without involving owner?")

    approving_member = models.ForeignKey(Member, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="permits_approved",
        help_text="The paying member who approved the parking of this item.")

    is_in_inventoried_space = models.BooleanField(default=True,
        help_text="True if the item is in our inventoried space/building(s). False if the owner has taken it home.")

    def __str__(self):
        return "P%04d, %s %s, '%s'" % (
            self.pk,
            self.owner.auth_user.first_name, self.owner.auth_user.last_name,
            self.short_desc)

    class Meta:
        ordering = ['owner', 'pk', 'created']
        unique_together = ('owner', 'created', 'short_desc')


class PermitRenewal(models.Model):

    # Intentionally NOT adding a "who" field. Only item owner should renew.

    permit = models.ForeignKey(ParkingPermit, null=False, blank=False,
        on_delete=models.CASCADE, related_name='renewals',
        help_text="The parking permit that was renewed.")

    when = models.DateField(null=False, blank=False,
        help_text="Date on which the parking permit was renewed.")

    def __str__(self):
        return "P%04d renewed on %s" % (self.permit.pk, self.when.isoformat())

    class Meta:
        ordering = ['permit', 'when']


class PermitScan(models.Model):

    # REVIEW: Is there a good balance between Admin presentation and making these fields editable=False?

    permit = models.ForeignKey(ParkingPermit, null=False, blank=False, on_delete=models.CASCADE, related_name='scans',
        help_text="The parking permit that was scanned")

    who = models.ForeignKey(Member, null=True, blank=True, on_delete=models.SET_NULL,
        help_text="The member who scanned the permit.")

    when = models.DateTimeField(null=False, blank=False,
        help_text="Date/time on which the parking permit was created.")

    where = models.ForeignKey(Location, null=False, blank=False, on_delete=models.PROTECT,
        help_text="The location at which the parking permit was scanned.")

    def __str__(self):
        p = self.permit
        return "P%04d at L%04d on %s" % (
            p.pk,
            self.where.pk,
            str(self.when.astimezone(timezone('US/Arizona')))[:10])

    class Meta:
        ordering = ['where','when']
