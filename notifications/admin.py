from django.contrib import admin
from .models import NotificationLog


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'channel', 'recipient', 'status', 'short_message')
    list_filter = ('channel', 'status')
    search_fields = ('recipient', 'message')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'channel', 'recipient', 'message', 'status', 'error_message', 'related_user')

    def short_message(self, obj):
        return obj.message[:60] + ('…' if len(obj.message) > 60 else '')
    short_message.short_description = 'Message'

    def has_add_permission(self, request):
        return False    # logs are system-generated

    def has_change_permission(self, request, obj=None):
        return False    # read-only
