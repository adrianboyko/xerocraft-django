# pylint: disable=C0330

# Standard
from pytz import timezone
from decimal import Decimal

# Third Party
from django.db import models
from django.utils import timezone as dutz

# Local
from members.models import Member


class Location(models.Model):

    x = models.FloatField(null=True, blank=True,
        help_text="An ordinate in some coordinate system to help locate the location.")

    y = models.FloatField(null=True, blank=True,
        help_text="An ordinate in some coordinate system to help locate the location.")

    z = models.FloatField(null=True, blank=True,
        help_text="An ordinate in some coordinate system to help locate the location.")

    short_desc = models.CharField(max_length=40, blank=False,
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

    public_info = models.URLField(null=True, blank=True,
        help_text="A link to the public wiki page about this shop.")

    def __str__(self):
        return self.name


class TaggedItem(models.Model):

    location = models.ForeignKey(Location, null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="The location of the item.")

    short_desc = models.CharField(max_length=40, blank=False,
        help_text="The items name or a short description.")

    created = models.DateField(null=False, blank=False, default=dutz.now,
        help_text="Date/time on which the item was tagged.")

    ok_to_move = models.BooleanField(default=True,
        help_text="Is it OK to carefully move the item to another location without involving owner?")

    is_in_inventoried_space = models.BooleanField(default=True,
        help_text="True if the item is in our inventoried space/building(s). False if the owner has taken it home.")

    class Meta:
        abstract = True


class Tool(TaggedItem):
    """Represents a tool, machine, etc. Not consumable."""

    shop = models.ForeignKey(Shop, null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="The shop that owns the tool.")

    public_info = models.URLField(null=True, blank=True,
        help_text="A link to the public wiki page about this tool.")

    TS_GOOD     = "G"  # The tool is in good shape.
    TS_DEGRADED = "D"  # The tool works but certain issues should be noted. See VALID ToolIssues.
    TS_UNUSABLE = "U"  # The tool cannot or should not be used. See VALID ToolIssues.
    TOOL_STATUS_CHOICES = [
        (TS_GOOD,     "Good"),
        (TS_DEGRADED, "Degraded"),
        (TS_UNUSABLE, "Unusable"),
    ]
    status = models.CharField(max_length=1, choices=TOOL_STATUS_CHOICES, default=TS_GOOD,
        help_text = "Status of the tool. If DEGRADED or UNUSABLE see Tool Issues.")

    is_loaned = models.BooleanField(default=False,
        help_text="Checked if this tool is on loan to us. Unchecked if we own it.")

    loaned_by = models.ForeignKey(Member, on_delete=models.PROTECT, null=True, default=None,
        help_text="If tool is loaned, this is the member who loaned it to us.")

    loan_terms = models.TextField(max_length=1024, default="",
        help_text="If tool is loaned, these are the terms specified by the loaner.")

    def __str__(self):
        toolname = self.short_desc if self.short_desc != "" else "?"
        shopname = self.shop.name if self.shop is not None and self.shop.name != "" else "?"
        return "{} in {}".format(toolname, shopname)


class ParkingPermit(TaggedItem):

    owner = models.ForeignKey(Member, null=False, blank=False, on_delete=models.PROTECT,
        related_name="permits_owned",
        help_text="The member who owns the parked item.")

    approving_member = models.ForeignKey(Member, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="permits_approved",
        help_text="The paying member who approved the parking of this item.")

    price_per_period = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False,
        default=Decimal("0.00"),
        help_text="The price per unit time for this permit.")

    PERIOD_NA      = "/"
    PERIOD_WEEK    = "W"
    PERIOD_MONTH   = "M"
    PERIOD_QUARTER = "Q"
    PERIOD_YEAR    = "Y"
    PERIOD_CHOICES = [
        (PERIOD_NA,      "N/A"),
        (PERIOD_WEEK,    "Weeks"),
        (PERIOD_MONTH,   "Months"),
        (PERIOD_QUARTER, "Quarters"),
        (PERIOD_YEAR,    "Years"),
    ]
    billing_period = models.CharField(max_length=1, choices=PERIOD_CHOICES, default=PERIOD_NA,
        help_text = "The price per period will be billed at this frequency.")

    def __str__(self):
        return "P%04d, %s %s, '%s'" % (
            self.pk,
            self.owner.auth_user.first_name, self.owner.auth_user.last_name,
            self.short_desc)


class ParkingPermitPayment(models.Model):

    # Intentionally NOT adding a "who" field. Only item owner should renew.

    permit = models.ForeignKey(ParkingPermit, null=False, blank=False,
        on_delete=models.CASCADE, related_name='renewals',
        help_text="The parking permit for which the payment was made.")

    start_date = models.DateField(null=False, blank=False,
        help_text="Permit is valid FROM this date, inclusive.")

    end_date = models.DateField(null=False, blank=False,
        help_text="Permit is valid TO this date, inclusive.")

    # TODO: Needs sale related fields.

    def __str__(self):
        values = (self.permit.pk, self.start_date.isoformat(), self.end_date.isoformat())
        return "P%04d payment %s to %s" % values

    class Meta:
        ordering = ['permit', 'start_date']


class PermitScan(models.Model):

    # REVIEW: Is there a good balance between Admin presentation and making these fields editable=False?

    permit = models.ForeignKey(ParkingPermit, null=False, blank=False, on_delete=models.CASCADE, related_name='scans',
        help_text="The parking permit that was scanned")

    who = models.ForeignKey(Member, null=True, blank=True, on_delete=models.SET_NULL,
        help_text="The member who scanned the permit.")

    when = models.DateTimeField(null=False, blank=False,
        help_text="Date/time on which the permit was scanned.")

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

#
# class RentedSpace(models.Model):
#


class ConsumableToStock(models.Model):

    short_desc = models.CharField(max_length=60, blank=False,
        help_text="The item's name or a short description.")

    obtain_from = models.CharField(max_length=40, blank=False,
        help_text="A suggested retailer to obtain the item from.")

    product_url = models.URLField(null=True, blank=True,
        help_text="If to be purchased online, specify an URL at the preferred store.")

    min_level = models.IntegerField(
        help_text="Restock when inventory reaches this low level.")

    min_level_unit = models.CharField(max_length=10, blank=False,
        help_text="Unit of restock.")

    for_shop = models.ForeignKey(Shop, null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="The shop that requested that this item be stocked.")

    restock_required = models.BooleanField(default=False,
        help_text="Set this if you notice that a restock is required.")

    stocker = models.ForeignKey(Member, null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="The Quartermaster if blank, else their delegate.")

    class Meta:
        verbose_name_plural = "Consumables to stock"