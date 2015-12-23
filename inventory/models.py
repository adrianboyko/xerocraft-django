from django.db import models
from members.models import Member
from pytz import timezone
import datetime


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


class ParkingPermit(models.Model):

    owner = models.ForeignKey(Member, null=False, blank=False, on_delete=models.PROTECT,
        help_text="The member who owns the parked item.")
    created = models.DateField(null=False, blank=False, auto_now_add=True,
        help_text="Date/time on which the parking permit was created.")
    short_desc = models.CharField(max_length=40, blank=False,
        help_text="A short description of the item parked.")
    ok_to_move = models.BooleanField(default=True,
        help_text="Is it OK to carefully move the item to another location, if necessary?")
    is_in_inventoried_space = models.BooleanField(default=True,
        help_text="True if the item is in our inventoried space/building(s). False if the owner has taken it home.")
    def __str__(self):
        return "P%04d, %s %s, '%s'" % (
            self.pk,
            self.owner.auth_user.first_name, self.owner.auth_user.last_name,
            self.short_desc)
    class Meta:
        ordering = ['owner', 'pk', 'created']


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
