"""
Health check endpoints for AI Measurement Service
"""

from fastapi import APIRouter, Depends
from datetime import datetime
import time
import psutil
import mediapipe as mp
import cv2

from ...models.schemas import HealthCheckResponse, ProcessingStats
from ...core.config import settings

router = APIRouter()

# Service start time for uptime calculation
SERVICE_START_TIME = time.time()

# Global stats tracking
processing_stats = ProcessingStats(
    total_requests=0,
    successful_requests=0,
    failed_requests=0,
    average_processing_time=0.0,
    uptime=0.0
)


@router.get("/", response_model=HealthCheckResponse)
async def health_check():
    """Basic health check endpoint"""
    
    # Check dependencies
    dependencies = {}
    
    try:
        # Check MediaPipe
        mp_pose = mp.solutions.pose
        dependencies["mediapipe"] = f"✅ {mp.__version__}"
    except Exception as e:
        dependencies["mediapipe"] = f"❌ Error: {str(e)}"
    
    try:
        # Check OpenCV
        dependencies["opencv"] = f"✅ {cv2.__version__}"
    except Exception as e:
        dependencies["opencv"] = f"❌ Error: {str(e)}"
    
    try:
        # Check system resources
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        dependencies["system"] = f"✅ CPU: {cpu_percent}% | Memory: {memory_percent}%"
    except Exception as e:
        dependencies["system"] = f"❌ Error: {str(e)}"
    
    return HealthCheckResponse(
        status="healthy",
        service="ai-measurement-service",
        version=settings.VERSION,
        dependencies=dependencies
    )


@router.get("/detailed", response_model=dict)
async def detailed_health_check():
    """Detailed health check with system information"""
    
    uptime = time.time() - SERVICE_START_TIME
    processing_stats.uptime = uptime
    
    try:
        # System information
        system_info = {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            } if hasattr(psutil.disk_usage('/'), 'total') else {}
        }
    except Exception as e:
        system_info = {"error": str(e)}
    
    # Service configuration
    service_config = {
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "model_complexity": settings.MEDIAPIPE_MODEL_COMPLEXITY,
        "min_detection_confidence": settings.MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
        "max_file_size": settings.MAX_FILE_SIZE,
        "allowed_image_types": settings.ALLOWED_IMAGE_TYPES
    }
    
    return {
        "status": "healthy",
        "service": "ai-measurement-service",
        "version": settings.VERSION,
        "uptime_seconds": uptime,
        "timestamp": datetime.now(),
        "system_info": system_info,
        "service_config": service_config,
        "processing_stats": processing_stats.dict(),
        "dependencies": {
            "mediapipe": mp.__version__,
            "opencv": cv2.__version__,
            "python": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}"
        }
    }


@router.get("/stats", response_model=ProcessingStats)
async def get_processing_stats():
    """Get processing statistics"""
    processing_stats.uptime = time.time() - SERVICE_START_TIME
    return processing_stats


def update_stats(success: bool, processing_time: float):
    """Update processing statistics"""
    global processing_stats
    
    processing_stats.total_requests += 1
    processing_stats.last_request_time = datetime.now()
    
    if success:
        processing_stats.successful_requests += 1
    else:
        processing_stats.failed_requests += 1
    
    # Update average processing time
    if processing_stats.total_requests > 0:
        current_total_time = processing_stats.average_processing_time * (processing_stats.total_requests - 1)
        new_total_time = current_total_time + processing_time
        processing_stats.average_processing_time = new_total_time / processing_stats.total_requests