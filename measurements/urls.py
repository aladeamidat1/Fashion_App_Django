from django.urls import path
from . import views

app_name = 'measurements'

urlpatterns = [
    # Measurement CRUD
    path('create/', views.MeasurementCreateView.as_view(), name='measurement_create'),
    path('list/', views.MeasurementListView.as_view(), name='measurement_list'),
    path('<int:pk>/', views.MeasurementDetailView.as_view(), name='measurement_detail'),
    path('<int:measurement_id>/history/', views.MeasurementHistoryView.as_view(), name='measurement_history'),
    
    # Quick measurement entry
    path('quick-entry/', views.quick_measurement_entry, name='quick_measurement_entry'),
    
    # Designer-Customer relationships
    path('relationships/', views.DesignerCustomerRelationshipListCreateView.as_view(), name='relationship_list_create'),
    path('relationships/<int:pk>/', views.DesignerCustomerRelationshipDetailView.as_view(), name='relationship_detail'),
    
    # Available connections
    path('available-customers/', views.available_customers, name='available_customers'),
    path('available-designers/', views.available_designers, name='available_designers'),
    
    # Dashboard
    path('dashboard/', views.measurement_dashboard, name='measurement_dashboard'),
]