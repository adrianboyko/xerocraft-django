from django.contrib import admin
from members.models import Member, Tag, Tagging, VisitEvent
from django.utils.translation import ugettext_lazy as _


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    fields = ['name','meaning']


@admin.register(Tagging)
class TaggingAdmin(admin.ModelAdmin):

    def members_username(self, object):
        return object.tagged_member.username
    members_username.admin_order_field = 'tagged_member__auth_user__username'
    raw_id_fields = ['tagged_member']
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

