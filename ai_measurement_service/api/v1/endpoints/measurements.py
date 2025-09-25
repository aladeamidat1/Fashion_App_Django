"""
Measurement endpoints for AI Measurement Service
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
import logging
import asyncio
import time
from typing import Optional, List
import os

from ...models.schemas import (
    ImageUploadRequest,
    AIMeasurementResponse,
    BatchProcessingRequest,
    BatchProcessingResponse,
    ErrorResponse
)
from ...services.body_measurement import BodyMeasurementService
from ...core.config import settings
from .health import update_stats

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize the measurement service
measurement_service = BodyMeasurementService()


@router.post("/extract", response_model=AIMeasurementResponse)
async def extract_measurements(request: ImageUploadRequest):
    """
    Extract body measurements from a single image
    
    Args:
        request: ImageUploadRequest containing base64 image data
        
    Returns:
        AIMeasurementResponse with extracted measurements
    """
    start_time = time.time()
    
    try:
        logger.info(f"Processing measurement extraction for customer {request.customer_id}")
        
        # Validate file size (estimate from base64)
        estimated_size = len(request.image_data) * 0.75  # Base64 is ~33% larger
        if estimated_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        # Validate image type
        if request.image_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image type. Allowed: {settings.ALLOWED_IMAGE_TYPES}"
            )
        
        # Process the image
        result = measurement_service.process_image(
            image_data=request.image_data,
            reference_height=request.reference_height
        )
        
        # Update statistics
        processing_time = time.time() - start_time
        update_stats(result.success, processing_time)
        
        if result.success:
            logger.info(f"Successfully extracted {len(result.measurements)} measurements in {processing_time:.2f}s")
        else:
            logger.warning(f"Failed to extract measurements: {result.errors}")
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions
        update_stats(False, time.time() - start_time)
        raise
    except Exception as e:
        # Handle unexpected errors
        processing_time = time.time() - start_time
        update_stats(False, processing_time)
        
        logger.error(f"Unexpected error in measurement extraction: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during measurement extraction: {str(e)}"
        )


@router.post("/extract-file", response_model=AIMeasurementResponse)
async def extract_measurements_from_file(
    file: UploadFile = File(...),
    customer_id: Optional[int] = Form(None),
    reference_height: Optional[float] = Form(None)
):
    """
    Extract body measurements from an uploaded file
    
    Args:
        file: Uploaded image file
        customer_id: Optional customer ID
        reference_height: Optional reference height in cm
        
    Returns:
        AIMeasurementResponse with extracted measurements
    """
    start_time = time.time()
    
    try:
        # Validate file size
        if file.size and file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        # Validate content type
        if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image type. Allowed: {settings.ALLOWED_IMAGE_TYPES}"
            )
        
        # Read and encode file data
        file_data = await file.read()
        import base64
        encoded_data = base64.b64encode(file_data).decode()
        
        # Create request object
        request = ImageUploadRequest(
            image_data=encoded_data,
            image_type=file.content_type,
            filename=file.filename or "uploaded_image",
            customer_id=customer_id,
            reference_height=reference_height
        )
        
        # Process the image
        result = measurement_service.process_image(
            image_data=request.image_data,
            reference_height=request.reference_height
        )
        
        # Update statistics
        processing_time = time.time() - start_time
        update_stats(result.success, processing_time)
        
        logger.info(f"Processed file upload: {file.filename}, Success: {result.success}")
        
        return result
        
    except HTTPException:
        update_stats(False, time.time() - start_time)
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        update_stats(False, processing_time)
        
        logger.error(f"Error processing uploaded file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing uploaded file: {str(e)}"
        )


@router.post("/batch", response_model=BatchProcessingResponse)
async def batch_extract_measurements(
    request: BatchProcessingRequest,
    background_tasks: BackgroundTasks
):
    """
    Extract measurements from multiple images in batch
    
    Args:
        request: BatchProcessingRequest with multiple images
        background_tasks: FastAPI background tasks
        
    Returns:
        BatchProcessingResponse with results for all images
    """
    batch_start_time = time.time()
    
    try:
        if len(request.images) > 10:  # Limit batch size
            raise HTTPException(
                status_code=400,
                detail="Batch size too large. Maximum 10 images per batch."
            )
        
        logger.info(f"Processing batch of {len(request.images)} images")
        
        results = []
        successful_extractions = 0
        failed_extractions = 0
        total_processing_time = 0.0
        
        # Process each image
        for i, image_request in enumerate(request.images):
            try:
                logger.info(f"Processing image {i+1}/{len(request.images)}")
                
                result = measurement_service.process_image(
                    image_data=image_request.image_data,
                    reference_height=image_request.reference_height
                )
                
                results.append(result)
                total_processing_time += result.processing_time
                
                if result.success:
                    successful_extractions += 1
                else:
                    failed_extractions += 1
                
            except Exception as e:
                logger.error(f"Error processing image {i+1}: {str(e)}")
                
                # Create error response for failed image
                error_result = AIMeasurementResponse(
                    success=False,
                    measurements=[],
                    image_width=0,
                    image_height=0,
                    processing_time=0.0,
                    pose_detection_confidence=0.0,
                    overall_accuracy=0.0,
                    errors=[f"Processing error: {str(e)}"]
                )
                results.append(error_result)
                failed_extractions += 1
        
        batch_processing_time = time.time() - batch_start_time
        average_processing_time = total_processing_time / len(request.images) if request.images else 0.0
        
        # Update global statistics for batch
        for result in results:
            update_stats(result.success, result.processing_time)
        
        response = BatchProcessingResponse(
            total_images=len(request.images),
            successful_extractions=successful_extractions,
            failed_extractions=failed_extractions,
            results=results,
            average_processing_time=average_processing_time,
            batch_processing_time=batch_processing_time
        )
        
        logger.info(f"Batch processing complete: {successful_extractions}/{len(request.images)} successful")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error in batch processing: {str(e)}"
        )


@router.get("/test", response_model=dict)
async def test_service():
    """
    Test endpoint to verify the service is working
    
    Returns:
        Test response with service status
    """
    return {
        "status": "operational",
        "service": "ai-measurement-service",
        "message": "Service is running and ready to process images",
        "endpoints": {
            "extract": "POST /api/v1/measurements/extract - Extract measurements from base64 image",
            "extract-file": "POST /api/v1/measurements/extract-file - Extract measurements from uploaded file",
            "batch": "POST /api/v1/measurements/batch - Batch process multiple images",
            "test": "GET /api/v1/measurements/test - Test service availability"
        },
        "requirements": {
            "image_types": settings.ALLOWED_IMAGE_TYPES,
            "max_file_size": f"{settings.MAX_FILE_SIZE / (1024*1024):.1f}MB",
            "max_batch_size": "10 images"
        }
    }


@router.get("/models/info", response_model=dict)
async def get_model_info():
    """
    Get information about the AI models being used
    
    Returns:
        Model configuration and capabilities
    """
    return {
        "mediapipe_pose": {
            "version": "0.10.0+",
            "model_complexity": settings.MEDIAPIPE_MODEL_COMPLEXITY,
            "min_detection_confidence": settings.MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
            "min_tracking_confidence": settings.MEDIAPIPE_MIN_TRACKING_CONFIDENCE,
            "supported_landmarks": 33,
            "capabilities": [
                "Full body pose detection",
                "Landmark visibility scoring",
                "Real-time processing"
            ]
        },
        "measurement_capabilities": {
            "supported_measurements": [
                "height", "shoulder_width", "arm_length", 
                "waist", "hips", "inseam", "torso_length"
            ],
            "accuracy_range": "70-90% depending on image quality",
            "recommended_conditions": [
                "Good lighting",
                "Plain background",
                "Fitted clothing",
                "Full body visible",
                "Standing straight"
            ]
        }
    }