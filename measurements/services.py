"""
Integration services for connecting with AI Measurement Service
"""

import requests
import logging
import json
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import Measurement, MeasurementHistory

User = get_user_model()
logger = logging.getLogger(__name__)


class AIMeasurementIntegrationService:
    """Service for integrating with AI Measurement microservice"""
    
    def __init__(self):
        """Initialize the integration service"""
        self.ai_service_url = getattr(settings, 'AI_MEASUREMENT_SERVICE_URL', 'http://localhost:8001/api/v1')
        self.timeout = getattr(settings, 'AI_SERVICE_TIMEOUT', 30)
        
    def extract_measurements_from_image(
        self, 
        image_data: str, 
        image_type: str,
        customer_id: int,
        reference_height: Optional[float] = None
    ) -> Dict:
        """
        Extract measurements from image using AI service
        
        Args:
            image_data: Base64 encoded image data
            image_type: MIME type of the image
            customer_id: ID of the customer
            reference_height: Optional reference height in cm
            
        Returns:
            Dict containing AI measurement results
        """
        try:
            payload = {
                "image_data": image_data,
                "image_type": image_type,
                "filename": f"customer_{customer_id}_measurement.jpg",
                "customer_id": customer_id,
                "reference_height": reference_height
            }
            
            logger.info(f"Sending measurement request to AI service for customer {customer_id}")
            
            response = requests.post(
                f"{self.ai_service_url}/measurements/extract",
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"AI service returned {len(result.get('measurements', []))} measurements")
                return result
            else:
                logger.error(f"AI service error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"AI service error: {response.status_code}",
                    "measurements": []
                }
                
        except requests.exceptions.Timeout:
            logger.error("AI service request timed out")
            return {
                "success": False,
                "error": "AI service request timed out",
                "measurements": []
            }
        except requests.exceptions.ConnectionError:
            logger.error("Could not connect to AI service")
            return {
                "success": False,
                "error": "AI service unavailable",
                "measurements": []
            }
        except Exception as e:
            logger.error(f"Unexpected error calling AI service: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "measurements": []
            }
    
    def create_measurement_from_ai_result(
        self,
        ai_result: Dict,
        customer: User,
        designer: User
    ) -> Tuple[Optional[Measurement], List[str]]:
        """
        Create a Measurement object from AI service results
        
        Args:
            ai_result: Results from AI measurement service
            customer: Customer user object
            designer: Designer user object
            
        Returns:
            Tuple of (Measurement object or None, list of errors)
        """
        errors = []
        
        try:
            if not ai_result.get('success', False):
                errors.append(f"AI measurement failed: {ai_result.get('error', 'Unknown error')}")
                return None, errors
            
            measurements_data = ai_result.get('measurements', [])
            if not measurements_data:
                errors.append("No measurements returned from AI service")
                return None, errors
            
            # Deactivate existing active measurements for this customer-designer pair
            Measurement.objects.filter(
                customer=customer,
                designer=designer,
                is_active=True
            ).update(is_active=False)
            
            # Create new measurement object
            measurement = Measurement(
                customer=customer,
                designer=designer,
                measurement_type='ai_generated',
                notes=f"AI-generated measurements. Confidence: {ai_result.get('overall_accuracy', 0):.2f}"
            )
            
            # Map AI measurements to model fields
            measurement_mapping = {
                'height': 'height',
                'shoulder_width': 'shoulder_width', 
                'arm_length': 'arm_length',
                'waist': 'waist',
                'hips': 'hips',
                'inseam': 'inseam',
                'bust': 'bust',
                'chest': 'chest',
                'torso_length': None,  # Custom field - we might add this later
            }
            
            applied_measurements = 0
            for ai_measurement in measurements_data:
                measurement_name = ai_measurement.get('name')
                measurement_value = ai_measurement.get('value')
                measurement_confidence = ai_measurement.get('confidence', 0)
                
                # Only apply measurements with reasonable confidence
                if measurement_confidence >= 0.5:
                    django_field = measurement_mapping.get(measurement_name)
                    if django_field and hasattr(measurement, django_field):
                        setattr(measurement, django_field, measurement_value)
                        applied_measurements += 1
                        logger.info(f"Applied {measurement_name}: {measurement_value}cm (confidence: {measurement_confidence:.2f})")
            
            if applied_measurements == 0:
                errors.append("No measurements had sufficient confidence to apply")
                return None, errors
            
            # Add metadata to notes
            metadata = ai_result.get('metadata', {})
            processing_time = ai_result.get('processing_time', 0)
            
            measurement.notes += f"\n\nAI Processing Details:"
            measurement.notes += f"\n- Processing time: {processing_time:.2f}s"
            measurement.notes += f"\n- Measurements applied: {applied_measurements}/{len(measurements_data)}"
            measurement.notes += f"\n- Pose confidence: {ai_result.get('pose_detection_confidence', 0):.2f}"
            
            # Add recommendations if available
            recommendations = ai_result.get('recommendations', [])
            if recommendations:
                measurement.notes += f"\n\nRecommendations:\n" + "\n".join(f"- {rec}" for rec in recommendations[:3])
            
            # Save the measurement
            measurement.save()
            
            logger.info(f"Created AI measurement record with {applied_measurements} measurements for customer {customer.id}")
            
            return measurement, errors
            
        except Exception as e:
            error_msg = f"Error creating measurement from AI result: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            return None, errors
    
    def validate_ai_measurements(
        self,
        measurement: Measurement,
        ai_result: Dict
    ) -> Dict:
        """
        Validate AI measurements against existing manual measurements
        
        Args:
            measurement: Measurement object to validate
            ai_result: Original AI service results
            
        Returns:
            Dict containing validation results
        """
        try:
            # Get the most recent manual measurement for comparison
            manual_measurement = Measurement.objects.filter(
                customer=measurement.customer,
                measurement_type='manual',
                is_active=True
            ).exclude(id=measurement.id).first()
            
            if not manual_measurement:
                return {
                    "validation_available": False,
                    "message": "No manual measurements available for comparison"
                }
            
            # Compare measurements
            comparisons = {}
            discrepancies = {}
            field_names = [
                'bust', 'waist', 'hips', 'chest', 'shoulder_width',
                'arm_length', 'height', 'inseam'
            ]
            
            total_discrepancy = 0
            compared_fields = 0
            
            for field in field_names:
                ai_value = getattr(measurement, field)
                manual_value = getattr(manual_measurement, field)
                
                if ai_value is not None and manual_value is not None:
                    difference = abs(ai_value - manual_value)
                    percentage_diff = (difference / manual_value) * 100 if manual_value > 0 else 0
                    
                    comparisons[field] = {
                        "ai_value": ai_value,
                        "manual_value": manual_value,
                        "difference": difference,
                        "percentage_difference": percentage_diff,
                        "acceptable": percentage_diff <= 10  # 10% tolerance
                    }
                    
                    discrepancies[field] = difference
                    total_discrepancy += percentage_diff
                    compared_fields += 1
            
            if compared_fields == 0:
                return {
                    "validation_available": False,
                    "message": "No comparable measurements found"
                }
            
            average_discrepancy = total_discrepancy / compared_fields
            accuracy_score = max(0, 100 - average_discrepancy) / 100  # Convert to 0-1 scale
            
            # Determine validation status
            acceptable_measurements = sum(1 for comp in comparisons.values() if comp["acceptable"])
            validation_passed = (acceptable_measurements / compared_fields) >= 0.7  # 70% must be acceptable
            
            return {
                "validation_available": True,
                "validation_passed": validation_passed,
                "accuracy_score": accuracy_score,
                "average_discrepancy_percentage": average_discrepancy,
                "compared_fields": compared_fields,
                "acceptable_measurements": acceptable_measurements,
                "comparisons": comparisons,
                "summary": {
                    "total_compared": compared_fields,
                    "acceptable": acceptable_measurements,
                    "accuracy": f"{accuracy_score*100:.1f}%",
                    "status": "PASSED" if validation_passed else "NEEDS_REVIEW"
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating AI measurements: {str(e)}")
            return {
                "validation_available": False,
                "error": f"Validation error: {str(e)}"
            }
    
    def check_ai_service_health(self) -> Dict:
        """
        Check if AI measurement service is available and healthy
        
        Returns:
            Dict containing health status
        """
        try:
            response = requests.get(
                f"{self.ai_service_url}/health/",
                timeout=5
            )
            
            if response.status_code == 200:
                health_data = response.json()
                return {
                    "available": True,
                    "status": health_data.get("status", "unknown"),
                    "service": health_data.get("service", "unknown"),
                    "version": health_data.get("version", "unknown")
                }
            else:
                return {
                    "available": False,
                    "error": f"Health check failed: {response.status_code}"
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "available": False,
                "error": "AI service unreachable"
            }
        except Exception as e:
            return {
                "available": False,
                "error": f"Health check error: {str(e)}"
            }


# Global instance
ai_measurement_service = AIMeasurementIntegrationService()