from rest_framework import serializers
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class UserCreateSerializer(BaseUserCreateSerializer):
    """
    Custom user creation serializer that includes role selection and additional fields
    """
    is_Designer = serializers.BooleanField(default=False)
    is_Customer = serializers.BooleanField(default=True)
    phone = serializers.CharField(max_length=11, required=True)
    
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 
            'phone', 'is_Designer', 'is_Customer', 'password'
        )
        
    def validate(self, attrs):
        # Ensure user has at least one role
        if not attrs.get('is_Designer') and not attrs.get('is_Customer'):
            raise serializers.ValidationError(
                "User must be either a Designer or Customer (or both)."
            )
        
        # Validate phone uniqueness
        phone = attrs.get('phone')
        if phone and User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError({
                'phone': 'This phone number is already in use.'
            })
            
        return super().validate(attrs)


class UserSerializer(BaseUserSerializer):
    """
    Custom user serializer for profile management
    """
    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'is_Designer', 'is_Customer', 'date_joined', 'last_login'
        )
        read_only_fields = ('id', 'date_joined', 'last_login')


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile information
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone')
        
    def validate_phone(self, value):
        # Check if phone number is unique (excluding current user)
        user = self.context['request'].user
        if User.objects.filter(phone=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("This phone number is already in use.")
        return value


class UserRoleUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user roles (Designer/Customer status)
    """
    class Meta:
        model = User
        fields = ('is_Designer', 'is_Customer')
        
    def validate(self, attrs):
        # Ensure user maintains at least one role
        current_user = self.context['request'].user
        is_designer = attrs.get('is_Designer', current_user.is_Designer)
        is_customer = attrs.get('is_Customer', current_user.is_Customer)
        
        if not is_designer and not is_customer:
            raise serializers.ValidationError(
                "User must maintain at least one role (Designer or Customer)."
            )
        return attrs