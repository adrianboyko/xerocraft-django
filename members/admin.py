from django.contrib import admin

from members.models import Member, Tag, Tagging, VisitEvent


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    fields = ['name','meaning']


@admin.register(Tagging)
class TaggingAdmin(admin.ModelAdmin):

    def members_username(self, object):
        return object.tagged_member.username
    members_username.admin_order_field = 'tagged_member__auth_user__username'

    list_display = ['pk', 'tagged_member', 'members_username', 'tag', 'can_tag', 'date_tagged', 'authorizing_member']
    search_fields = [
        '^tagged_member__auth_user__first_name',
        '^tagged_member__auth_user__last_name',
        'tag__name',
        '^tagged_member__auth_user__username',
    ]


@admin.register(VisitEvent)
class VisitEventAdmin(admin.ModelAdmin):
    list_display = ['pk', 'when', 'who', 'event_type', 'sync1']
    readonly_fields = ['when', 'who', 'event_type', 'sync1']
    search_fields = [
        '^who__auth_user__first_name',
        '^who__auth_user__last_name',
    ]
    list_filter = ['when']
    date_hierarchy = 'when'


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['pk', '__str__', 'auth_user', 'membership_card_when', 'membership_card_md5']
    search_fields = [
        '^auth_user__first_name',
        '^auth_user__last_name',
        '^auth_user__username',
    ]

