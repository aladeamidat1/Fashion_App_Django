from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView
from django.contrib.auth import get_user_model
from .serializers import (
    UserSerializer, 
    UserProfileUpdateSerializer, 
    UserRoleUpdateSerializer
)

User = get_user_model()


class UserProfileView(RetrieveUpdateAPIView):
    """
    View for retrieving and updating user profile
    """
    serializer_class = UserProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserSerializer
        return UserProfileUpdateSerializer


class UserRoleUpdateView(APIView):
    """
    View for updating user roles (Designer/Customer status)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request):
        serializer = UserRoleUpdateSerializer(
            instance=request.user,
            data=request.data,
            context={'request': request},
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            user_data = UserSerializer(request.user).data
            return Response({
                'message': 'User roles updated successfully',
                'user': user_data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_dashboard(request):
    """
    Dashboard endpoint that returns user-specific information based on their role
    """
    user = request.user
    user_data = UserSerializer(user).data
    
    dashboard_data = {
        'user': user_data,
        'role_info': {
            'is_designer': user.is_Designer,
            'is_customer': user.is_Customer,
        }
    }
    
    # Add role-specific data
    if user.is_Designer:
        # In future phases, add designer-specific data like customer count, measurements, etc.
        dashboard_data['designer_stats'] = {
            'total_customers': 0,  # Will be implemented when measurements app is created
            'pending_measurements': 0,
        }
    
    if user.is_Customer:
        # In future phases, add customer-specific data like measurements, orders, etc.
        dashboard_data['customer_stats'] = {
            'measurements_recorded': 0,  # Will be implemented when measurements app is created
            'assigned_designers': 0,
        }
    
    return Response(dashboard_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def designers_list(request):
    """
    Endpoint to list all designers (accessible to customers for designer selection)
    """
    if not request.user.is_Customer:
        return Response(
            {'error': 'Only customers can access the designers list'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    designers = User.objects.filter(is_Designer=True, is_active=True)
    designers_data = []
    
    for designer in designers:
        designers_data.append({
            'id': designer.id,
            'username': designer.username,
            'first_name': designer.first_name,
            'last_name': designer.last_name,
            'email': designer.email,
            # In future phases, add ratings, specializations, etc.
        })
    
    return Response({
        'designers': designers_data,
        'count': len(designers_data)
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def customers_list(request):
    """
    Endpoint to list customers (accessible to designers)
    """
    if not request.user.is_Designer:
        return Response(
            {'error': 'Only designers can access the customers list'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    customers = User.objects.filter(is_Customer=True, is_active=True)
    customers_data = []
    
    for customer in customers:
        customers_data.append({
            'id': customer.id,
            'username': customer.username,
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'email': customer.email,
            'phone': customer.phone,
            # In future phases, add measurement status, order history, etc.
        })
    
    return Response({
        'customers': customers_data,
        'count': len(customers_data)
    }, status=status.HTTP_200_OK)
