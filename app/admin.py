from django.contrib import admin

from .models import InBox, Message

class MessageAdmin(admin.ModelAdmin):
    actions = None

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(InBox)
admin.site.register(Message, MessageAdmin)
