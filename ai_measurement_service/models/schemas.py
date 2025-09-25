"""
Pydantic models for AI Measurement Service
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
import base64


class ImageUploadRequest(BaseModel):
    """Request model for image upload"""
    image_data: str = Field(..., description="Base64 encoded image data")
    image_type: str = Field(..., description="Image MIME type (e.g., image/jpeg)")
    filename: str = Field(..., description="Original filename")
    customer_id: Optional[int] = Field(None, description="Customer ID from Django app")
    reference_height: Optional[float] = Field(None, description="Reference height in cm")
    
    @validator('image_data')
    def validate_image_data(cls, v):
        """Validate base64 image data"""
        try:
            # Remove data URL prefix if present
            if ',' in v:
                v = v.split(',')[1]
            base64.b64decode(v)
            return v
        except Exception:
            raise ValueError("Invalid base64 image data")
    
    @validator('image_type')
    def validate_image_type(cls, v):
        """Validate image MIME type"""
        allowed_types = ["image/jpeg", "image/jpg", "image/png"]
        if v.lower() not in allowed_types:
            raise ValueError(f"Image type must be one of: {allowed_types}")
        return v.lower()


class BodyLandmark(BaseModel):
    """Individual body landmark point"""
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate") 
    z: Optional[float] = Field(None, description="Z coordinate (depth)")
    visibility: Optional[float] = Field(None, description="Landmark visibility score")


class BodyLandmarks(BaseModel):
    """Collection of body landmarks detected by MediaPipe"""
    landmarks: List[BodyLandmark] = Field(..., description="List of body landmarks")
    pose_confidence: float = Field(..., description="Overall pose detection confidence")
    timestamp: datetime = Field(default_factory=datetime.now)


class MeasurementResult(BaseModel):
    """Individual measurement result"""
    name: str = Field(..., description="Measurement name (e.g., 'bust', 'waist')")
    value: float = Field(..., description="Measurement value in centimeters")
    confidence: float = Field(..., description="Confidence score (0-1)")
    method: str = Field(..., description="Calculation method used")


class AIMeasurementResponse(BaseModel):
    """Response model for AI measurement extraction"""
    success: bool = Field(..., description="Whether measurement extraction was successful")
    measurements: List[MeasurementResult] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Image processing info
    image_width: int = Field(..., description="Processed image width")
    image_height: int = Field(..., description="Processed image height")
    processing_time: float = Field(..., description="Processing time in seconds")
    
    # Quality metrics
    pose_detection_confidence: float = Field(..., description="Pose detection confidence")
    overall_accuracy: float = Field(..., description="Overall measurement accuracy estimate")
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for better measurements")
    
    # Error information
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
    warnings: List[str] = Field(default_factory=list, description="Warnings about measurement quality")


class MeasurementValidation(BaseModel):
    """Model for validating AI measurements against manual measurements"""
    ai_measurements: Dict[str, float] = Field(..., description="AI-generated measurements")
    manual_measurements: Optional[Dict[str, float]] = Field(None, description="Manual measurements for comparison")
    validation_score: Optional[float] = Field(None, description="Validation score (0-1)")
    discrepancies: Dict[str, float] = Field(default_factory=dict, description="Differences between AI and manual")


class BatchProcessingRequest(BaseModel):
    """Request model for batch processing multiple images"""
    images: List[ImageUploadRequest] = Field(..., description="List of images to process")
    customer_id: Optional[int] = Field(None, description="Customer ID")
    processing_options: Dict[str, Any] = Field(default_factory=dict, description="Processing options")


class BatchProcessingResponse(BaseModel):
    """Response model for batch processing"""
    total_images: int = Field(..., description="Total number of images processed")
    successful_extractions: int = Field(..., description="Number of successful extractions")
    failed_extractions: int = Field(..., description="Number of failed extractions")
    results: List[AIMeasurementResponse] = Field(..., description="Individual results")
    average_processing_time: float = Field(..., description="Average processing time per image")
    batch_processing_time: float = Field(..., description="Total batch processing time")


class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.now)
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Dependency status")


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now)


class MeasurementCalibration(BaseModel):
    """Model for measurement calibration data"""
    reference_object_pixels: float = Field(..., description="Reference object size in pixels")
    reference_object_real_size: float = Field(..., description="Reference object real size in cm")
    pixel_to_cm_ratio: float = Field(..., description="Calculated pixel to cm ratio")
    calibration_confidence: float = Field(..., description="Calibration confidence score")


class ProcessingStats(BaseModel):
    """Processing statistics model"""
    total_requests: int = Field(default=0, description="Total number of requests processed")
    successful_requests: int = Field(default=0, description="Number of successful requests")
    failed_requests: int = Field(default=0, description="Number of failed requests")
    average_processing_time: float = Field(default=0.0, description="Average processing time")
    uptime: float = Field(..., description="Service uptime in seconds")
    last_request_time: Optional[datetime] = Field(None, description="Timestamp of last request")