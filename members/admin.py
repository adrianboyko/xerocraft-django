from django.contrib import admin
from members.models import Member, Tag, Tagging, VisitEvent, PaidMembership, PaymentAKA
from django.utils.translation import ugettext_lazy as _


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    fields = ['name','meaning']


@admin.register(Tagging)
class TaggingAdmin(admin.ModelAdmin):

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
class VisitEventAdmin(admin.ModelAdmin):
    list_display = ['pk', 'when', 'who', 'event_type', 'method', 'sync1']
    readonly_fields = ['when', 'who', 'event_type', 'method', 'sync1']
    search_fields = [
        '^who__auth_user__first_name',
        '^who__auth_user__last_name',
        '^who__auth_user__username',
    ]
    list_filter = ['when']
    date_hierarchy = 'when'


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


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):

    list_display = ['pk', '__str__', 'auth_user', 'membership_card_when', 'membership_card_md5']

    search_fields = [
        '^auth_user__first_name',
        '^auth_user__last_name',
        '^auth_user__username',
    ]

    list_display_links = ['pk', '__str__']

    list_filter = [MemberTypeFilter]


PAYMENT_METHOD_CODE2STR = {code: str for (code, str) in PaidMembership.PAID_BY_CHOICES}
MEMBERSHIP_TYPE_CODE2STR = {code: str for (code, str) in PaidMembership.MEMBERSHIP_TYPE_CHOICES}


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


@admin.register(PaidMembership)
class PaidMembershipAdmin(admin.ModelAdmin):

    date_hierarchy = 'payment_date'
    list_filter = [PaymentLinkedFilter, 'payment_method']

    def fam_fmt(self,obj): return obj.family_count
    fam_fmt.admin_order_field = 'family_count'
    fam_fmt.short_description = 'fam'

    def paid_fmt(self,obj): return obj.paid_by_member
    paid_fmt.admin_order_field = 'paid_by_member'
    paid_fmt.short_description = 'paid'

    def fee_fmt(self,obj): return obj.processing_fee
    fee_fmt.admin_order_field = 'processing_fee'
    fee_fmt.short_description = 'fee'

    def type_fmt(self,obj): return MEMBERSHIP_TYPE_CODE2STR[obj.membership_type]
    type_fmt.admin_order_field = 'membership_type'
    type_fmt.short_description = 'type'

    def when_fmt(self,obj): return obj.payment_date
    when_fmt.admin_order_field = 'payment_date'
    when_fmt.short_description = 'when'

    def how_fmt(self,obj): return PAYMENT_METHOD_CODE2STR[obj.payment_method]
    how_fmt.admin_order_field = 'payment_method'
    how_fmt.short_description = 'how'

    list_display = [
        'pk',
        'member',
        'type_fmt',
        'fam_fmt',
        'start_date',
        'end_date',

        'payer_name',
        'payer_email',
        'paid_fmt',
        'fee_fmt',
        'when_fmt',
        'how_fmt',
    ]

    fieldsets = [
        ('Membership Details', {'fields': [
            'member',
            'membership_type',
            'family_count',
            'start_date',
            'end_date',
        ]}),
        ('Payment Details', {'fields': [
            'payer_name',
            'payer_email',
            'paid_by_member',
            'processing_fee',
            'payment_date',
            'payment_method',
            'ctrlid',
        ]}),
    ]

    raw_id_fields = ['member']
    search_fields = [
        '^member__auth_user__first_name',
        '^member__auth_user__last_name',
        '^member__auth_user__username',
        'payer_name',
        'payer_email',
    ]


@admin.register(PaymentAKA)
class MemberAKAAdmin(admin.ModelAdmin):
    list_display = ['pk', 'member', 'aka']
    raw_id_fields = ['member']
