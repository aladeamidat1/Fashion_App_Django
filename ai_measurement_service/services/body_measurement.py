"""
Body measurement extraction service using MediaPipe and OpenCV
"""

import cv2
import numpy as np
import mediapipe as mp
import logging
import time
from typing import Dict, List, Tuple, Optional
from PIL import Image
import io
import base64

from ..models.schemas import (
    BodyLandmarks, 
    BodyLandmark, 
    MeasurementResult, 
    AIMeasurementResponse,
    MeasurementCalibration
)
from ..core.config import settings

logger = logging.getLogger(__name__)


class BodyMeasurementService:
    """Service for extracting body measurements from images using AI"""
    
    def __init__(self):
        """Initialize MediaPipe and OpenCV components"""
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Initialize pose detection
        self.pose = self.mp_pose.Pose(
            model_complexity=settings.MEDIAPIPE_MODEL_COMPLEXITY,
            min_detection_confidence=settings.MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=settings.MEDIAPIPE_MIN_TRACKING_CONFIDENCE
        )
        
        logger.info("BodyMeasurementService initialized")
    
    def process_image(self, image_data: str, reference_height: Optional[float] = None) -> AIMeasurementResponse:
        """
        Process an image and extract body measurements
        
        Args:
            image_data: Base64 encoded image data
            reference_height: Reference height in cm for calibration
            
        Returns:
            AIMeasurementResponse with extracted measurements
        """
        start_time = time.time()
        
        try:
            # Decode image
            image = self._decode_image(image_data)
            original_height, original_width = image.shape[:2]
            
            # Convert BGR to RGB for MediaPipe
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Process pose detection
            results = self.pose.process(rgb_image)
            
            if not results.pose_landmarks:
                return AIMeasurementResponse(
                    success=False,
                    measurements=[],
                    image_width=original_width,
                    image_height=original_height,
                    processing_time=time.time() - start_time,
                    pose_detection_confidence=0.0,
                    overall_accuracy=0.0,
                    errors=["No pose detected in image"],
                    recommendations=[
                        "Ensure the person is fully visible in the image",
                        "Use good lighting conditions",
                        "Make sure the person is standing straight"
                    ]
                )
            
            # Extract landmarks
            landmarks = self._extract_landmarks(results.pose_landmarks, original_width, original_height)
            
            # Calculate measurements
            measurements, calibration = self._calculate_measurements(
                landmarks, 
                original_width, 
                original_height,
                reference_height
            )
            
            # Calculate overall confidence and accuracy
            pose_confidence = self._calculate_pose_confidence(results.pose_landmarks)
            overall_accuracy = self._estimate_accuracy(measurements, pose_confidence)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(measurements, pose_confidence)
            
            processing_time = time.time() - start_time
            
            return AIMeasurementResponse(
                success=True,
                measurements=measurements,
                metadata={
                    "landmarks_count": len(landmarks.landmarks),
                    "calibration": calibration.dict() if calibration else None,
                    "mediapipe_version": mp.__version__,
                    "model_complexity": settings.MEDIAPIPE_MODEL_COMPLEXITY
                },
                image_width=original_width,
                image_height=original_height,
                processing_time=processing_time,
                pose_detection_confidence=pose_confidence,
                overall_accuracy=overall_accuracy,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return AIMeasurementResponse(
                success=False,
                measurements=[],
                image_width=0,
                image_height=0,
                processing_time=time.time() - start_time,
                pose_detection_confidence=0.0,
                overall_accuracy=0.0,
                errors=[f"Processing error: {str(e)}"]
            )
    
    def _decode_image(self, image_data: str) -> np.ndarray:
        """Decode base64 image data to OpenCV format"""
        try:
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            # Decode base64
            image_bytes = base64.b64decode(image_data)
            
            # Convert to PIL Image
            pil_image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to OpenCV format
            opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            return opencv_image
            
        except Exception as e:
            raise ValueError(f"Failed to decode image: {str(e)}")
    
    def _extract_landmarks(self, pose_landmarks, width: int, height: int) -> BodyLandmarks:
        """Extract body landmarks from MediaPipe results"""
        landmarks = []
        
        for landmark in pose_landmarks.landmark:
            landmarks.append(BodyLandmark(
                x=landmark.x * width,
                y=landmark.y * height,
                z=landmark.z,
                visibility=landmark.visibility
            ))
        
        return BodyLandmarks(
            landmarks=landmarks,
            pose_confidence=self._calculate_pose_confidence(pose_landmarks)
        )
    
    def _calculate_measurements(
        self, 
        landmarks: BodyLandmarks, 
        width: int, 
        height: int,
        reference_height: Optional[float] = None
    ) -> Tuple[List[MeasurementResult], Optional[MeasurementCalibration]]:
        """Calculate body measurements from landmarks"""
        
        measurements = []
        calibration = None
        
        # MediaPipe pose landmark indices
        LANDMARK_INDICES = {
            'nose': 0,
            'left_eye_inner': 1, 'left_eye': 2, 'left_eye_outer': 3,
            'right_eye_inner': 4, 'right_eye': 5, 'right_eye_outer': 6,
            'left_ear': 7, 'right_ear': 8,
            'mouth_left': 9, 'mouth_right': 10,
            'left_shoulder': 11, 'right_shoulder': 12,
            'left_elbow': 13, 'right_elbow': 14,
            'left_wrist': 15, 'right_wrist': 16,
            'left_pinky': 17, 'right_pinky': 18,
            'left_index': 19, 'right_index': 20,
            'left_thumb': 21, 'right_thumb': 22,
            'left_hip': 23, 'right_hip': 24,
            'left_knee': 25, 'right_knee': 26,
            'left_ankle': 27, 'right_ankle': 28,
            'left_heel': 29, 'right_heel': 30,
            'left_foot_index': 31, 'right_foot_index': 32
        }
        
        # Extract key landmarks
        lms = landmarks.landmarks
        
        try:
            # Calculate pixel-to-cm ratio using reference height or estimated height
            if reference_height:
                # Use provided reference height
                head_to_ankle = self._calculate_distance(
                    lms[LANDMARK_INDICES['nose']],
                    lms[LANDMARK_INDICES['left_ankle']]
                )
                pixel_to_cm_ratio = reference_height / head_to_ankle
                
                calibration = MeasurementCalibration(
                    reference_object_pixels=head_to_ankle,
                    reference_object_real_size=reference_height,
                    pixel_to_cm_ratio=pixel_to_cm_ratio,
                    calibration_confidence=0.9
                )
            else:
                # Estimate height based on average human proportions
                head_to_ankle = self._calculate_distance(
                    lms[LANDMARK_INDICES['nose']],
                    lms[LANDMARK_INDICES['left_ankle']]
                )
                estimated_height = settings.REFERENCE_HEIGHT_CM  # Default 170cm
                pixel_to_cm_ratio = estimated_height / head_to_ankle
                
                calibration = MeasurementCalibration(
                    reference_object_pixels=head_to_ankle,
                    reference_object_real_size=estimated_height,
                    pixel_to_cm_ratio=pixel_to_cm_ratio,
                    calibration_confidence=0.7  # Lower confidence for estimated height
                )
            
            # Calculate body measurements
            
            # 1. Height
            height_pixels = self._calculate_distance(
                lms[LANDMARK_INDICES['nose']],
                lms[LANDMARK_INDICES['left_ankle']]
            )
            measurements.append(MeasurementResult(
                name="height",
                value=height_pixels * pixel_to_cm_ratio,
                confidence=0.9,
                method="nose_to_ankle_distance"
            ))
            
            # 2. Shoulder width
            shoulder_width = self._calculate_distance(
                lms[LANDMARK_INDICES['left_shoulder']],
                lms[LANDMARK_INDICES['right_shoulder']]
            )
            measurements.append(MeasurementResult(
                name="shoulder_width",
                value=shoulder_width * pixel_to_cm_ratio,
                confidence=0.85,
                method="shoulder_to_shoulder_distance"
            ))
            
            # 3. Arm length (shoulder to wrist)
            left_arm_length = self._calculate_distance(
                lms[LANDMARK_INDICES['left_shoulder']],
                lms[LANDMARK_INDICES['left_wrist']]
            )
            measurements.append(MeasurementResult(
                name="arm_length",
                value=left_arm_length * pixel_to_cm_ratio,
                confidence=0.8,
                method="shoulder_to_wrist_distance"
            ))
            
            # 4. Estimated waist (hip width as approximation)
            hip_width = self._calculate_distance(
                lms[LANDMARK_INDICES['left_hip']],
                lms[LANDMARK_INDICES['right_hip']]
            )
            # Waist is typically 70-80% of hip width
            estimated_waist = hip_width * 0.75
            measurements.append(MeasurementResult(
                name="waist",
                value=estimated_waist * pixel_to_cm_ratio,
                confidence=0.6,  # Lower confidence as this is estimated
                method="hip_width_estimation"
            ))
            
            # 5. Hip width
            measurements.append(MeasurementResult(
                name="hips",
                value=hip_width * pixel_to_cm_ratio,
                confidence=0.8,
                method="hip_to_hip_distance"
            ))
            
            # 6. Inseam (hip to ankle)
            inseam = self._calculate_distance(
                lms[LANDMARK_INDICES['left_hip']],
                lms[LANDMARK_INDICES['left_ankle']]
            )
            measurements.append(MeasurementResult(
                name="inseam",
                value=inseam * pixel_to_cm_ratio,
                confidence=0.85,
                method="hip_to_ankle_distance"
            ))
            
            # 7. Torso length (shoulder to hip)
            torso_length = self._calculate_distance(
                lms[LANDMARK_INDICES['left_shoulder']],
                lms[LANDMARK_INDICES['left_hip']]
            )
            measurements.append(MeasurementResult(
                name="torso_length",
                value=torso_length * pixel_to_cm_ratio,
                confidence=0.8,
                method="shoulder_to_hip_distance"
            ))
            
        except Exception as e:
            logger.error(f"Error calculating measurements: {str(e)}")
            # Return basic measurements even if some calculations fail
            pass
        
        return measurements, calibration
    
    def _calculate_distance(self, point1: BodyLandmark, point2: BodyLandmark) -> float:
        """Calculate Euclidean distance between two landmarks"""
        return np.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)
    
    def _calculate_pose_confidence(self, pose_landmarks) -> float:
        """Calculate overall pose detection confidence"""
        if not pose_landmarks:
            return 0.0
        
        # Calculate average visibility of key landmarks
        key_landmark_indices = [0, 11, 12, 23, 24, 25, 26, 27, 28]  # Key body points
        total_visibility = 0.0
        valid_landmarks = 0
        
        for i in key_landmark_indices:
            if i < len(pose_landmarks.landmark):
                total_visibility += pose_landmarks.landmark[i].visibility
                valid_landmarks += 1
        
        if valid_landmarks == 0:
            return 0.0
        
        return total_visibility / valid_landmarks
    
    def _estimate_accuracy(self, measurements: List[MeasurementResult], pose_confidence: float) -> float:
        """Estimate overall measurement accuracy"""
        if not measurements:
            return 0.0
        
        # Calculate weighted average of measurement confidences
        total_confidence = sum(m.confidence for m in measurements)
        avg_measurement_confidence = total_confidence / len(measurements)
        
        # Combine with pose confidence
        overall_accuracy = (avg_measurement_confidence * 0.7) + (pose_confidence * 0.3)
        
        return min(overall_accuracy, 1.0)
    
    def _generate_recommendations(self, measurements: List[MeasurementResult], pose_confidence: float) -> List[str]:
        """Generate recommendations for improving measurement accuracy"""
        recommendations = []
        
        if pose_confidence < 0.7:
            recommendations.append("Improve lighting conditions for better pose detection")
            recommendations.append("Ensure the person is standing straight and facing the camera")
        
        if pose_confidence < 0.5:
            recommendations.append("Consider retaking the photo with the person more clearly visible")
        
        # Check measurement confidence
        low_confidence_measurements = [m for m in measurements if m.confidence < 0.7]
        if low_confidence_measurements:
            recommendations.append("Some measurements have lower confidence - consider manual verification")
        
        if len(measurements) < 5:
            recommendations.append("Limited measurements detected - ensure full body is visible in the image")
        
        recommendations.append("For best results, use a photo with the person standing against a plain background")
        recommendations.append("Ensure the person is wearing fitted clothing for more accurate measurements")
        
        return recommendations
    
    def __del__(self):
        """Cleanup MediaPipe resources"""
        if hasattr(self, 'pose'):
            self.pose.close()