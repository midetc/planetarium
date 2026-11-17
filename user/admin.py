from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()


class ModUserAdmin(UserAdmin):
    ordering = ("email",)
    list_display = ("email", "is_staff")
    add_fieldsets = (
        (
            None, {
            'fields': ('email', 'password1', 'password2'),
        },
        ),
    )
    fieldsets = (
        (
            None, {
            'fields': ('email', 'password', 'is_staff', "is_active", "is_superuser"),
        },
        ),
    )


admin.site.register(User, ModUserAdmin)
