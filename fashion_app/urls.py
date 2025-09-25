"""
URL configuration for fashion_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

# Create a router for API endpoints
router = routers.DefaultRouter()

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API root
    path('api/', include(router.urls)),
    
    # Authentication endpoints (Djoser + JWT)
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),
    
    # User management endpoints
    path('api/users/', include('users.urls')),
    
    # Measurement management endpoints
    path('api/measurements/', include('measurements.urls')),
    
    # API documentation (optional - you can add swagger later)
    # path('api/docs/', include_docs_urls(title='Fashion App API')),
]
