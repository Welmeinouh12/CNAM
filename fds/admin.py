from django.contrib import admin

from .models import EmailVerificationCode


@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    """Consultation des codes envoyés (création/suppression désactivées)."""

    list_display = ('email', 'code', 'attempts', 'created_at', 'expires_at', 'consumed_at')
    list_filter = ('created_at',)
    search_fields = ('email',)
    readonly_fields = ('email', 'code', 'attempts', 'created_at', 'expires_at', 'consumed_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

