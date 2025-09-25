from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # User profile management
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('role/update/', views.UserRoleUpdateView.as_view(), name='update_user_role'),
    
    # Dashboard
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    
    # Lists for role-based access
    path('designers/', views.designers_list, name='designers_list'),
    path('customers/', views.customers_list, name='customers_list'),
]