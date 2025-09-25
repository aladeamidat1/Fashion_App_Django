from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

User = get_user_model()


class Measurement(models.Model):
    """
    Model to store body measurements for customers
    """
    # Relationship fields
    customer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='measurements',
        limit_choices_to={'is_Customer': True}
    )
    designer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='customer_measurements',
        limit_choices_to={'is_Designer': True}
    )
    
    # Measurement fields (in centimeters)
    # Upper body measurements
    bust = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(300)],
        help_text="Bust measurement in centimeters",
        null=True, blank=True
    )
    waist = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(300)],
        help_text="Waist measurement in centimeters",
        null=True, blank=True
    )
    hips = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(300)],
        help_text="Hip measurement in centimeters",
        null=True, blank=True
    )
    chest = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(300)],
        help_text="Chest measurement in centimeters",
        null=True, blank=True
    )
    shoulder_width = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Shoulder width in centimeters",
        null=True, blank=True
    )
    
    # Arm measurements
    arm_length = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(150)],
        help_text="Arm length in centimeters",
        null=True, blank=True
    )
    sleeve_length = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(150)],
        help_text="Sleeve length in centimeters",
        null=True, blank=True
    )
    bicep = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Bicep measurement in centimeters",
        null=True, blank=True
    )
    forearm = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        help_text="Forearm measurement in centimeters",
        null=True, blank=True
    )
    wrist = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(30)],
        help_text="Wrist measurement in centimeters",
        null=True, blank=True
    )
    
    # Leg measurements
    inseam = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(150)],
        help_text="Inseam measurement in centimeters",
        null=True, blank=True
    )
    outseam = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(200)],
        help_text="Outseam measurement in centimeters",
        null=True, blank=True
    )
    thigh = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(150)],
        help_text="Thigh measurement in centimeters",
        null=True, blank=True
    )
    calf = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Calf measurement in centimeters",
        null=True, blank=True
    )
    ankle = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        help_text="Ankle measurement in centimeters",
        null=True, blank=True
    )
    
    # General measurements
    height = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(300)],
        help_text="Height in centimeters",
        null=True, blank=True
    )
    weight = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(500)],
        help_text="Weight in kilograms",
        null=True, blank=True
    )
    neck = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Neck measurement in centimeters",
        null=True, blank=True
    )
    
    # Metadata
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the measurements"
    )
    measurement_type = models.CharField(
        max_length=20,
        choices=[
            ('manual', 'Manual Entry'),
            ('ai_generated', 'AI Generated'),
            ('hybrid', 'AI + Manual Correction')
        ],
        default='manual'
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this measurement record is currently active"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = ['customer', 'designer', 'is_active']
        
    def __str__(self):
        return f"Measurements for {self.customer.get_full_name()} by {self.designer.get_full_name()}"
    
    def get_completion_percentage(self):
        """
        Calculate what percentage of measurements have been recorded
        """
        measurement_fields = [
            'bust', 'waist', 'hips', 'chest', 'shoulder_width',
            'arm_length', 'sleeve_length', 'bicep', 'forearm', 'wrist',
            'inseam', 'outseam', 'thigh', 'calf', 'ankle',
            'height', 'weight', 'neck'
        ]
        
        total_fields = len(measurement_fields)
        completed_fields = sum(1 for field in measurement_fields if getattr(self, field) is not None)
        
        return (completed_fields / total_fields) * 100 if total_fields > 0 else 0
    
    def get_basic_measurements(self):
        """
        Return the most essential measurements for clothing design
        """
        return {
            'bust': self.bust,
            'waist': self.waist,
            'hips': self.hips,
            'height': self.height,
            'sleeve_length': self.sleeve_length,
            'inseam': self.inseam
        }


class MeasurementHistory(models.Model):
    """
    Model to track changes in measurements over time
    """
    measurement = models.ForeignKey(
        Measurement,
        on_delete=models.CASCADE,
        related_name='history'
    )
    field_name = models.CharField(max_length=50)
    old_value = models.FloatField(null=True)
    new_value = models.FloatField(null=True)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    changed_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(
        max_length=100,
        blank=True,
        help_text="Reason for the change"
    )
    
    class Meta:
        ordering = ['-changed_at']
        
    def __str__(self):
        return f"{self.field_name} changed from {self.old_value} to {self.new_value}"


class DesignerCustomerRelationship(models.Model):
    """
    Model to manage the relationship between designers and customers
    """
    designer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='customer_relationships',
        limit_choices_to={'is_Designer': True}
    )
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='designer_relationships',
        limit_choices_to={'is_Customer': True}
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('blocked', 'Blocked')
        ],
        default='pending'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['designer', 'customer']
        ordering = ['-updated_at']
        
    def __str__(self):
        return f"{self.designer.get_full_name()} - {self.customer.get_full_name()} ({self.status})"
