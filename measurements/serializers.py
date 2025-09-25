from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Measurement, MeasurementHistory, DesignerCustomerRelationship

User = get_user_model()


class MeasurementCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new measurement records
    """
    class Meta:
        model = Measurement
        fields = [
            'customer', 'bust', 'waist', 'hips', 'chest', 'shoulder_width',
            'arm_length', 'sleeve_length', 'bicep', 'forearm', 'wrist',
            'inseam', 'outseam', 'thigh', 'calf', 'ankle',
            'height', 'weight', 'neck', 'notes', 'measurement_type'
        ]
        
    def create(self, validated_data):
        # Automatically assign the designer from the authenticated user
        validated_data['designer'] = self.context['request'].user
        
        # Deactivate any existing active measurements for this customer-designer pair
        Measurement.objects.filter(
            customer=validated_data['customer'],
            designer=validated_data['designer'],
            is_active=True
        ).update(is_active=False)
        
        return super().create(validated_data)
    
    def validate_customer(self, value):
        """Ensure the customer is actually a customer user"""
        if not value.is_Customer:
            raise serializers.ValidationError("Selected user is not a customer.")
        return value


class MeasurementDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for measurement records with related user information
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    designer_name = serializers.CharField(source='designer.get_full_name', read_only=True)
    completion_percentage = serializers.SerializerMethodField()
    basic_measurements = serializers.SerializerMethodField()
    
    class Meta:
        model = Measurement
        fields = [
            'id', 'customer', 'designer', 'customer_name', 'designer_name',
            'bust', 'waist', 'hips', 'chest', 'shoulder_width',
            'arm_length', 'sleeve_length', 'bicep', 'forearm', 'wrist',
            'inseam', 'outseam', 'thigh', 'calf', 'ankle',
            'height', 'weight', 'neck', 'notes', 'measurement_type',
            'is_active', 'completion_percentage', 'basic_measurements',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'designer']
    
    def get_completion_percentage(self, obj):
        return round(obj.get_completion_percentage(), 2)
    
    def get_basic_measurements(self, obj):
        return obj.get_basic_measurements()


class MeasurementUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating measurement records
    """
    class Meta:
        model = Measurement
        fields = [
            'bust', 'waist', 'hips', 'chest', 'shoulder_width',
            'arm_length', 'sleeve_length', 'bicep', 'forearm', 'wrist',
            'inseam', 'outseam', 'thigh', 'calf', 'ankle',
            'height', 'weight', 'neck', 'notes', 'measurement_type'
        ]
    
    def update(self, instance, validated_data):
        # Track changes in measurement history
        user = self.context['request'].user
        
        for field, new_value in validated_data.items():
            old_value = getattr(instance, field)
            if old_value != new_value and field not in ['notes', 'measurement_type']:
                MeasurementHistory.objects.create(
                    measurement=instance,
                    field_name=field,
                    old_value=old_value,
                    new_value=new_value,
                    changed_by=user
                )
        
        return super().update(instance, validated_data)


class MeasurementHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for measurement history records
    """
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    
    class Meta:
        model = MeasurementHistory
        fields = [
            'id', 'field_name', 'old_value', 'new_value',
            'changed_by', 'changed_by_name', 'changed_at', 'reason'
        ]
        read_only_fields = ['id', 'changed_at']


class DesignerCustomerRelationshipSerializer(serializers.ModelSerializer):
    """
    Serializer for designer-customer relationships
    """
    designer_name = serializers.CharField(source='designer.get_full_name', read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    designer_email = serializers.EmailField(source='designer.email', read_only=True)
    customer_email = serializers.EmailField(source='customer.email', read_only=True)
    
    class Meta:
        model = DesignerCustomerRelationship
        fields = [
            'id', 'designer', 'customer', 'designer_name', 'customer_name',
            'designer_email', 'customer_email', 'status', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        # Ensure the designer is actually a designer
        if 'designer' in attrs and not attrs['designer'].is_Designer:
            raise serializers.ValidationError({
                'designer': 'Selected user is not a designer.'
            })
        
        # Ensure the customer is actually a customer
        if 'customer' in attrs and not attrs['customer'].is_Customer:
            raise serializers.ValidationError({
                'customer': 'Selected user is not a customer.'
            })
        
        return attrs


class CustomerMeasurementSummarySerializer(serializers.ModelSerializer):
    """
    Simplified serializer for displaying customer measurement summaries
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_email = serializers.EmailField(source='customer.email', read_only=True)
    completion_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Measurement
        fields = [
            'id', 'customer', 'customer_name', 'customer_email',
            'completion_percentage', 'measurement_type', 'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']
    
    def get_completion_percentage(self, obj):
        return round(obj.get_completion_percentage(), 2)


class BasicMeasurementSerializer(serializers.ModelSerializer):
    """
    Serializer for basic measurements only (for quick entry)
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    
    class Meta:
        model = Measurement
        fields = [
            'id', 'customer', 'customer_name', 'bust', 'waist', 'hips',
            'height', 'sleeve_length', 'inseam', 'notes'
        ]
        read_only_fields = ['id']