from django.contrib import admin
from .models import Measurement, MeasurementHistory, DesignerCustomerRelationship


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    """
    Admin interface for Measurement model
    """
    list_display = [
        'customer', 'designer', 'measurement_type', 'completion_percentage_display',
        'is_active', 'updated_at'
    ]
    list_filter = [
        'measurement_type', 'is_active', 'designer', 'created_at', 'updated_at'
    ]
    search_fields = [
        'customer__username', 'customer__email', 'customer__first_name', 
        'customer__last_name', 'designer__username', 'designer__email',
        'designer__first_name', 'designer__last_name'
    ]
    readonly_fields = ['created_at', 'updated_at', 'completion_percentage_display']
    
    fieldsets = (
        ('Relationship', {
            'fields': ('customer', 'designer', 'measurement_type', 'is_active')
        }),
        ('Upper Body Measurements', {
            'fields': ('bust', 'waist', 'hips', 'chest', 'shoulder_width', 'neck'),
            'classes': ('collapse',)
        }),
        ('Arm Measurements', {
            'fields': ('arm_length', 'sleeve_length', 'bicep', 'forearm', 'wrist'),
            'classes': ('collapse',)
        }),
        ('Leg Measurements', {
            'fields': ('inseam', 'outseam', 'thigh', 'calf', 'ankle'),
            'classes': ('collapse',)
        }),
        ('General Measurements', {
            'fields': ('height', 'weight')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completion_percentage_display'),
            'classes': ('collapse',)
        })
    )
    
    def completion_percentage_display(self, obj):
        return f"{obj.get_completion_percentage():.1f}%"
    completion_percentage_display.short_description = 'Completion %'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer', 'designer')


@admin.register(MeasurementHistory)
class MeasurementHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for MeasurementHistory model
    """
    list_display = [
        'measurement', 'field_name', 'old_value', 'new_value', 
        'changed_by', 'changed_at'
    ]
    list_filter = ['field_name', 'changed_at', 'changed_by']
    search_fields = [
        'measurement__customer__username', 'measurement__designer__username',
        'field_name', 'changed_by__username'
    ]
    readonly_fields = ['changed_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'measurement__customer', 'measurement__designer', 'changed_by'
        )


@admin.register(DesignerCustomerRelationship)
class DesignerCustomerRelationshipAdmin(admin.ModelAdmin):
    """
    Admin interface for DesignerCustomerRelationship model
    """
    list_display = [
        'designer', 'customer', 'status', 'created_at', 'updated_at'
    ]
    list_filter = ['status', 'created_at', 'updated_at']
    search_fields = [
        'designer__username', 'designer__email', 'designer__first_name',
        'designer__last_name', 'customer__username', 'customer__email',
        'customer__first_name', 'customer__last_name'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Relationship', {
            'fields': ('designer', 'customer', 'status')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('designer', 'customer')
