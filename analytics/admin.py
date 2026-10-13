from django.contrib import admin
from .models import PageVisit


@admin.register(PageVisit)
class PageVisitAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'path', 'is_bot', 'user', 'session_key_short')
    list_filter = ('is_bot', 'created_at')
    search_fields = ('path', 'user_agent', 'ip_hash')
    date_hierarchy = 'created_at'
    readonly_fields = (
        'path', 'method', 'ip_hash', 'user_agent', 'referer',
        'session_key', 'user', 'is_bot', 'created_at',
    )

    def session_key_short(self, obj):
        return (obj.session_key or '')[:12]
    session_key_short.short_description = 'Session'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
