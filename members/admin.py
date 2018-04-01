
# Standard

# Third Party
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse

from reversion.admin import VersionAdmin

# Local
from books.admin import Sellable, Invoiceable, sale_link
from members.models import (
    Tag, Pushover, Tagging, VisitEvent,
    Member, Membership, GroupMembership, KeyFee, ExternalId,
    MemberNote, MemberLogin, MembershipGiftCardRedemption,
    MembershipGiftCard, MembershipGiftCardReference, MembershipCampaign,
    DiscoveryMethod
)


@admin.register(Tag)
class TagAdmin(VersionAdmin):

    list_display = ['pk', 'name', 'meaning']

    fields = ['name', 'meaning']

    search_fields = ['name', 'meaning']


@admin.register(Tagging)
class TaggingAdmin(VersionAdmin):

    def members_username(self, object):
        return object.tagged_member.username
    members_username.admin_order_field = 'tagged_member__auth_user__username'
    raw_id_fields = ['tagged_member', 'authorizing_member']
    list_display = ['pk', 'tagged_member', 'members_username', 'tag', 'can_tag', 'date_tagged', 'authorizing_member']
    search_fields = [
        '^tagged_member__auth_user__first_name',
        '^tagged_member__auth_user__last_name',
        'tag__name',
        '^tagged_member__auth_user__username',
    ]


@admin.register(VisitEvent)
class VisitEventAdmin(admin.ModelAdmin):  # No need to version events.

    def has_add_permission(self, request):
        return False
        # Don't allow humans to add these. They are created by automated processes.

    def who_username(self, object):
        return object.who.username

    ordering = ['-when']
    list_display = ['pk', 'when', 'who_username', 'who', 'event_type', 'reason', 'method']
    #readonly_fields = ['when', 'who', 'event_type', 'method']
    search_fields = [
        '^who__auth_user__first_name',
        '^who__auth_user__last_name',
        '^who__auth_user__username',
    ]
    list_filter = ['when', 'event_type', 'reason', 'method']
    date_hierarchy = 'when'
    raw_id_fields = ['who']


class MemberTypeFilter(admin.SimpleListFilter):
    title = "Worker Type"
    parameter_name = 'type'

    def lookups(self, request, model_admin):
        return (
            ('worktrade', _('Work-Trader')),
            ('intern', _('Intern')),
            ('scholar', _('Scholarship')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'worktrade': return queryset.filter(tags__name="Work-Trader")
        if self.value() == 'intern':    return queryset.filter(tags__name="Intern")
        if self.value() == 'scholar':   return queryset.filter(tags__name="Scholarship")


class TaggingForMember(admin.TabularInline):
    model = Tagging
    fk_name = 'tagged_member'
    raw_id_fields = ['authorizing_member']
    # model._meta.verbose_name = "Tag"
    # model._meta.verbose_name_plural = "Tags"
    extra = 0


class MemberNoteInline(admin.TabularInline):
    model = MemberNote
    fk_name = 'member'
    raw_id_fields = ['author']
    extra = 0


@admin.register(Member)
class MemberAdmin(VersionAdmin):

    def has_add_permission(self, request):
        return False
        # Add users instead, which drives creation of a Member.

    def has_delete_permission(self, request, obj=None):
        return False
        # Deactivate users instead.

    class MembershipInline(admin.TabularInline):
        model = Membership
        extra = 0
        fields = [
            'membership_type',
            'start_date',
            'end_date',
            'when_nudged',
            'nudge_count',
        ]
        readonly_fields = [
            'membership_type',
            'start_date',
            'end_date',
            'when_nudged',
            'nudge_count',
        ]

    class PushoverInline(admin.TabularInline):
        model = Pushover
        extra = 0
        fields = ['who', 'mechanism', 'key']

    def _active(self, obj) -> bool:
        return obj.auth_user.is_active
    _active.boolean = True
    _active.short_description = 'active'

    list_display = [
        'pk',
        '_active',
        'username',
        'first_name',
        'last_name',
        'email',
        'is_adult'
        # 'membership_card_when',
        # 'membership_card_md5'
    ]

    fields = [
        'auth_user',
        'membership_card_md5',
        # 'membership_card_when',
        'nag_re_membership',
        'is_adult',
        'birth_date',
        'discovery',
    ]

    readonly_fields = ['discovery']

    raw_id_fields = ['auth_user']

    search_fields = [
        '^auth_user__first_name',
        '^auth_user__last_name',
        '^auth_user__username',
        'auth_user__email',
        '^membership_card_md5',
    ]

    list_display_links = [
        'pk',
        'username',
        'first_name',
        'last_name',
        'email',
    ]

    list_filter = [MemberTypeFilter, 'is_adult']

    inlines = [MemberNoteInline, TaggingForMember, PushoverInline, MembershipInline]

    class Media:
        css = {
            "all": ("abutils/admin-tabular-inline.css",)  # This hides "denormalized object descs", to use Woj's term.
        }


MEMBERSHIP_TYPE_CODE2STR = {code: str for (code, str) in Membership.MEMBERSHIP_TYPE_CHOICES}


class PaymentLinkedFilter(admin.SimpleListFilter):
    title = "Linked"
    parameter_name = 'type'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Yes')),
            ('no', _('No')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes': return queryset.filter(member__isnull=False)
        if self.value() == 'no':  return queryset.filter(member__isnull=True)


# @admin.register(PaymentAKA)
# class MemberAKAAdmin(VersionAdmin):
#     list_display = ['pk', 'member', 'aka']
#     raw_id_fields = ['member']


@admin.register(MemberLogin)
class MemberLoginAdmin(VersionAdmin):

    def has_add_permission(self, request):
        return False
        # These are created by automated processes, not humans.

    list_display = ['pk', 'member', 'when', 'ip']
    raw_id_fields = ['member']
    ordering = ['-when']


@admin.register(MembershipCampaign)
class MembershipCampaignAdmin(VersionAdmin):

    list_display = [
        'pk',
        'name',
        'description',
    ]

    list_display_links = [
        'pk',
        'name',
    ]


@admin.register(MembershipGiftCard)
class MembershipGiftCardAdmin(VersionAdmin):

    def sold(self, obj):
        ref = obj.membershipgiftcardreference
        if ref is None: return None
        return ref.sale.sale_date

    def created(self, obj):
        return obj.date_created

    def redeemed(self, obj):
        redemp = obj.membershipgiftcardredemption
        if redemp is None: return None
        return redemp.redemption_date

    list_display = [
        'pk',
        'redemption_code',
        'campaign',
        'price',
        'month_duration',
        'day_duration',
        'created',
        'sold',
        'redeemed',
    ]
    date_hierarchy = 'date_created'
    search_fields = ['redemption_code']
    list_display_links = ['pk', 'redemption_code']
    list_filter = ['month_duration', 'day_duration', 'price']
    ordering = ['redemption_code']


@admin.register(MembershipGiftCardRedemption)
class MembershipGiftCardRedemptionAdmin(VersionAdmin):

    class MembershipInline(admin.StackedInline):
        model = Membership
        extra = 0
        fields = [
            'member',
            'membership_type',
            ('start_date', 'end_date'),
        ]
        raw_id_fields = ['member']

    def members(self, obj):
        return ",".join([str(mli.member) for mli in obj.membership_set.all()])

    list_display = ['pk', 'members', 'card']
    search_fields = ['card__redemption_code']
    inlines = [
        MembershipInline,
    ]
    raw_id_fields = ['card']


@admin.register(Membership)
class MembershipAdmin(VersionAdmin):

    def has_add_permission(self, request):
        return False
        # Create an IncomeTransaction (Sale) instead, with membership as a line item.

    def has_delete_permission(self, request, obj=None):
        return False
        # Don't. Deleting these messes up bookkeeping.

    ordering = ['-start_date']
    date_hierarchy = 'start_date'
    list_filter = [
        'membership_type',
        'protected',
    ]

    def type_fmt(self,obj): return MEMBERSHIP_TYPE_CODE2STR[obj.membership_type]
    type_fmt.admin_order_field = 'membership_type'
    type_fmt.short_description = 'type'

    def src_fmt(self,obj):
        if obj.sale is not None: return str(obj.sale)
        if obj.redemption is not None: return "Gift card "+obj.redemption.card.redemption_code
        if obj.group is not None: return "Member of {} group".format(obj.group.group_tag)
        else: return None
    src_fmt.short_description = 'source'

    list_display = [
        'pk',
        'member',
        'type_fmt',
        'start_date',
        'end_date',
        'sale_price',
        'src_fmt',
    ]

    fields = [
        'member',
        'membership_type',
        ('start_date', 'end_date'),
        'sale_price',
        ('when_nudged', 'nudge_count'),
        'sale', 'group',
        'protected',
        'ctrlid',
    ]

    readonly_fields = ['ctrlid']
    raw_id_fields = ['member', 'sale', 'group']

    search_fields = [
        'pk',
        '^member__auth_user__first_name',
        '^member__auth_user__last_name',
        '^member__auth_user__username',
        'sale__payer_name',
        'sale__payer_email',
    ]


@admin.register(GroupMembership)
class GroupMembershipAdmin(VersionAdmin):

    def has_add_permission(self, request):
        return False
        # Create an IncomeTransaction (Sale) instead, with group membership as a line item.

    def has_delete_permission(self, request, obj=None):
        return False
        # Don't. Deleting these messes up bookkeeping.

    class MembershipInline(admin.TabularInline):
        model = Membership
        extra = 0
        fields = [
            'member',
            'membership_type',
            'start_date',
            'end_date'
        ]
        raw_id_fields = ['member']
        readonly_fields = ['membership_type', 'start_date', 'end_date']

    inlines = [MembershipInline]

    list_display = [
        'pk',
        'sale_price',
        'group_tag',
        'start_date',
        'end_date',
        'max_members',
    ]

    list_filter = [
        ('group_tag', admin.RelatedOnlyFieldListFilter),
    ]

    date_hierarchy = 'start_date'

    fields = [
        'sale_price',
        'group_tag',
        ('start_date', 'end_date'),
        'max_members',
    ]

    class Media:
        css = {
            "all": ("abutils/admin-tabular-inline.css",)
        }


#@admin.register(KeyFee)
class KeyFeeAdmin(VersionAdmin):

    sale_link = sale_link  # imported from books

    list_display = [
        'pk',
        'sale_price',
        'membership',
        'start_date',
        'end_date',
        'sale_link',
    ]

    fields = [
        'sale_price',
        'membership',
        ('start_date', 'end_date'),
        'sale_link',
    ]

    raw_id_fields = ['membership',]
    readonly_fields = ['sale_price']

    def has_add_permission(self, request):
        return False
        # Instead, create an IncomeTransaction (Sale) with key fee as a line item.

    def has_delete_permission(self, request, obj=None):
        return False
        # Deleting would mess up bookkeeping.

    # def has_change_permission(self, request, obj=None):
    # I want to make these read only through KeyFeeAdmin, but then they completely vanish.


@admin.register(DiscoveryMethod)
class DiscoveryMethodAdmin(VersionAdmin):

    list_display = ['pk', 'order', 'name', 'visible']

    list_filter = ['visible']

    ordering = ['order']


@admin.register(ExternalId)
class ExternalIdAdmin(VersionAdmin):

    list_display = ['pk', 'provider', 'uid', 'user', 'extra_data']

    raw_id_fields = ['user']

    search_fields = ['user__username', 'uid']

    list_filter = ['provider']


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Line-Item Inlines for SaleAdmin in Books app.
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@Sellable(MembershipGiftCardReference)
class MembershipGiftCardLineItem(admin.StackedInline):
    fields = [
        'sale_price',
        'card',
    ]
    extra = 0
    raw_id_fields = ['card']


@Sellable(Membership)
class MembershipLineItem(admin.StackedInline):
    extra = 0
    fields = [
        'sale_price',
        'member',
        'membership_type',
        ('start_date', 'end_date'),
        'protected',
    ]
    raw_id_fields = ['member']


@Sellable(KeyFee)
class KeeFeeLineItem(admin.StackedInline):
    extra = 0
    fields = [
        'sale_price',
        'membership',
        ('start_date', 'end_date'),
        'protected',
    ]
    raw_id_fields = ['membership']


@Invoiceable(GroupMembership)
@Sellable(GroupMembership)
class GroupMembershipLineItem(admin.StackedInline):
    extra = 0

    def details(self, obj):
        app = obj._meta.app_label
        mod = obj._meta.model_name
        url_str = reverse('admin:{}_{}_change'.format(app, mod), args=(obj.id,))
        return format_html("<a href='{}'>View All Group Membership Info</a>", url_str)

    fields = [
        'sale_price',
        'group_tag',
        ('start_date', 'end_date'),
        'max_members',
        'details'
    ]

    readonly_fields = ['details']