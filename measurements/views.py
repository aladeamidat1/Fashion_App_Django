from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import Measurement, MeasurementHistory, DesignerCustomerRelationship
from .serializers import (
    MeasurementCreateSerializer,
    MeasurementDetailSerializer,
    MeasurementUpdateSerializer,
    MeasurementHistorySerializer,
    DesignerCustomerRelationshipSerializer,
    CustomerMeasurementSummarySerializer,
    BasicMeasurementSerializer
)

User = get_user_model()


class MeasurementCreateView(generics.CreateAPIView):
    """
    Create new measurement records (Designers only)
    """
    serializer_class = MeasurementCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        if not self.request.user.is_Designer:
            raise permissions.PermissionDenied("Only designers can create measurements.")
        serializer.save(designer=self.request.user)


class MeasurementListView(generics.ListAPIView):
    """
    List measurements based on user role
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.query_params.get('summary') == 'true':
            return CustomerMeasurementSummarySerializer
        return MeasurementDetailSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_Designer:
            # Designers see measurements for their customers
            return Measurement.objects.filter(
                designer=user,
                is_active=True
            ).select_related('customer', 'designer')
        
        elif user.is_Customer:
            # Customers see their own measurements
            return Measurement.objects.filter(
                customer=user,
                is_active=True
            ).select_related('customer', 'designer')
        
        else:
            return Measurement.objects.none()


class MeasurementDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a specific measurement
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return MeasurementUpdateSerializer
        return MeasurementDetailSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_Designer:
            return Measurement.objects.filter(designer=user)
        elif user.is_Customer:
            return Measurement.objects.filter(customer=user)
        else:
            return Measurement.objects.none()
    
    def perform_update(self, serializer):
        # Only designers can update measurements
        if not self.request.user.is_Designer:
            raise permissions.PermissionDenied("Only designers can update measurements.")
        serializer.save()
    
    def perform_destroy(self, instance):
        # Only designers can delete measurements (actually just deactivate)
        if not self.request.user.is_Designer:
            raise permissions.PermissionDenied("Only designers can delete measurements.")
        instance.is_active = False
        instance.save()


class MeasurementHistoryView(generics.ListAPIView):
    """
    View measurement history for a specific measurement
    """
    serializer_class = MeasurementHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        measurement_id = self.kwargs.get('measurement_id')
        measurement = get_object_or_404(Measurement, id=measurement_id)
        
        # Check permissions
        user = self.request.user
        if not (measurement.designer == user or measurement.customer == user):
            return MeasurementHistory.objects.none()
        
        return MeasurementHistory.objects.filter(
            measurement=measurement
        ).select_related('changed_by')


class DesignerCustomerRelationshipListCreateView(generics.ListCreateAPIView):
    """
    List and create designer-customer relationships
    """
    serializer_class = DesignerCustomerRelationshipSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_Designer:
            return DesignerCustomerRelationship.objects.filter(
                designer=user
            ).select_related('customer', 'designer')
        elif user.is_Customer:
            return DesignerCustomerRelationship.objects.filter(
                customer=user
            ).select_related('customer', 'designer')
        else:
            return DesignerCustomerRelationship.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        
        if user.is_Designer:
            serializer.save(designer=user)
        elif user.is_Customer:
            serializer.save(customer=user)
        else:
            raise permissions.PermissionDenied("Invalid user role for creating relationships.")


class DesignerCustomerRelationshipDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Manage specific designer-customer relationships
    """
    serializer_class = DesignerCustomerRelationshipSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        return DesignerCustomerRelationship.objects.filter(
            Q(designer=user) | Q(customer=user)
        ).select_related('customer', 'designer')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def measurement_dashboard(request):
    """
    Dashboard view with measurement statistics
    """
    user = request.user
    
    if user.is_Designer:
        # Designer dashboard
        total_customers = DesignerCustomerRelationship.objects.filter(
            designer=user, status='active'
        ).count()
        
        total_measurements = Measurement.objects.filter(
            designer=user, is_active=True
        ).count()
        
        pending_measurements = Measurement.objects.filter(
            designer=user, is_active=True
        ).filter(
            Q(bust__isnull=True) | Q(waist__isnull=True) | 
            Q(hips__isnull=True) | Q(height__isnull=True)
        ).count()
        
        recent_measurements = Measurement.objects.filter(
            designer=user, is_active=True
        ).select_related('customer').order_by('-updated_at')[:5]
        
        data = {
            'role': 'designer',
            'stats': {
                'total_customers': total_customers,
                'total_measurements': total_measurements,
                'pending_measurements': pending_measurements,
                'completion_rate': round(
                    ((total_measurements - pending_measurements) / total_measurements * 100) 
                    if total_measurements > 0 else 0, 2
                )
            },
            'recent_measurements': CustomerMeasurementSummarySerializer(
                recent_measurements, many=True
            ).data
        }
    
    elif user.is_Customer:
        # Customer dashboard
        active_designers = DesignerCustomerRelationship.objects.filter(
            customer=user, status='active'
        ).count()
        
        my_measurements = Measurement.objects.filter(
            customer=user, is_active=True
        ).count()
        
        recent_updates = Measurement.objects.filter(
            customer=user, is_active=True
        ).select_related('designer').order_by('-updated_at')[:3]
        
        avg_completion = 0
        if my_measurements > 0:
            measurements = Measurement.objects.filter(customer=user, is_active=True)
            total_completion = sum(m.get_completion_percentage() for m in measurements)
            avg_completion = round(total_completion / my_measurements, 2)
        
        data = {
            'role': 'customer',
            'stats': {
                'active_designers': active_designers,
                'my_measurements': my_measurements,
                'avg_completion': avg_completion
            },
            'recent_updates': MeasurementDetailSerializer(
                recent_updates, many=True
            ).data
        }
    
    else:
        return Response(
            {'error': 'Invalid user role'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    return Response(data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def quick_measurement_entry(request):
    """
    Quick entry for basic measurements
    """
    if not request.user.is_Designer:
        return Response(
            {'error': 'Only designers can enter measurements'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = BasicMeasurementSerializer(data=request.data)
    if serializer.is_valid():
        # Check if measurement already exists for this customer-designer pair
        existing = Measurement.objects.filter(
            customer=serializer.validated_data['customer'],
            designer=request.user,
            is_active=True
        ).first()
        
        if existing:
            # Update existing measurement
            for field, value in serializer.validated_data.items():
                if field != 'customer' and value is not None:
                    setattr(existing, field, value)
            existing.save()
            return Response(
                MeasurementDetailSerializer(existing).data,
                status=status.HTTP_200_OK
            )
        else:
            # Create new measurement
            measurement = serializer.save(designer=request.user)
            return Response(
                MeasurementDetailSerializer(measurement).data,
                status=status.HTTP_201_CREATED
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def available_customers(request):
    """
    Get list of customers available to connect with (for designers)
    """
    if not request.user.is_Designer:
        return Response(
            {'error': 'Only designers can access this endpoint'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get customers not already connected to this designer
    connected_customers = DesignerCustomerRelationship.objects.filter(
        designer=request.user
    ).values_list('customer_id', flat=True)
    
    available_customers = User.objects.filter(
        is_Customer=True,
        is_active=True
    ).exclude(id__in=connected_customers)
    
    customers_data = []
    for customer in available_customers:
        customers_data.append({
            'id': customer.id,
            'username': customer.username,
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'email': customer.email,
            'full_name': customer.get_full_name()
        })
    
    return Response({
        'available_customers': customers_data,
        'count': len(customers_data)
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def available_designers(request):
    """
    Get list of designers available to connect with (for customers)
    """
    if not request.user.is_Customer:
        return Response(
            {'error': 'Only customers can access this endpoint'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get designers not already connected to this customer
    connected_designers = DesignerCustomerRelationship.objects.filter(
        customer=request.user
    ).values_list('designer_id', flat=True)
    
    available_designers = User.objects.filter(
        is_Designer=True,
        is_active=True
    ).exclude(id__in=connected_designers)
    
    designers_data = []
    for designer in available_designers:
        designers_data.append({
            'id': designer.id,
            'username': designer.username,
            'first_name': designer.first_name,
            'last_name': designer.last_name,
            'email': designer.email,
            'full_name': designer.get_full_name()
        })
    
    return Response({
        'available_designers': designers_data,
        'count': len(designers_data)
    })
