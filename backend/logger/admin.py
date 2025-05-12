from django.contrib import admin
from .models import ErrorLog

@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'level', 'source', 'component', 'message_preview')
    list_filter = ('level', 'source', 'timestamp')
    search_fields = ('message', 'component')
    readonly_fields = ('id', 'timestamp')
    
    def message_preview(self, obj):
        """Return a truncated version of the message for display in list view"""
        if len(obj.message) > 100:
            return f"{obj.message[:100]}..."
        return obj.message
    
    message_preview.short_description = 'Message'
    
    fieldsets = (
        (None, {
            'fields': ('id', 'timestamp', 'level', 'source')
        }),
        ('Error Details', {
            'fields': ('component', 'message', 'traceback')
        }),
        ('Additional Data', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
