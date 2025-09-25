from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User admin with role fields
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone', 'is_Designer', 'is_Customer', 'is_staff')
    list_filter = ('is_Designer', 'is_Customer', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone')
    ordering = ('username',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role Information', {'fields': ('is_Designer', 'is_Customer')}),
        ('Contact Information', {'fields': ('phone',)}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role Information', {'fields': ('is_Designer', 'is_Customer')}),
        ('Contact Information', {'fields': ('phone', 'email')}),
    )

