"""
Enhanced Document Processor with Comprehensive Error Handling
Implements graceful degradation and fallback mechanisms for document processing
"""

from typing import Dict, Any, Optional
import numpy as np
from services.document_processor import DocumentProcessor, DocumentType, DocumentQuality
from shared.utils.error_handling import (
    DocumentProcessingError,
    ErrorSeverity,
    with_retry,
    handle_error,
    error_message_generator
)
import logging

logger = logging.getLogger(__name__)


class EnhancedDocumentProcessor(DocumentProcessor):
    """
    Enhanced document processor with error handling and fallback mechanisms
    """
    
    def __init__(self):
        super().__init__()
        self.fallback_mode = False
        self.manual_review_queue = []
    
    def process_document_safe(
        self,
        image_data: np.ndarray,
        document_type: DocumentType,
        user_profile: Optional[Dict[str, Any]] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Process document with comprehensive error handling
        
        Args:
            image_data: Image as numpy array
            document_type: Type of document
            user_profile: Optional user profile for validation
            language: User's preferred language for error messages
            
        Returns:
            Processing result with fallback handling
        """
        try:
            # Validate input
            if image_data is None or image_data.size == 0:
                raise DocumentProcessingError(
                    message="Image data is empty or invalid",
                    severity=ErrorSeverity.MEDIUM,
                    user_message=error_message_generator.get_message("doc_unreadable", language),
                    suggested_actions=[
                        "Please upload a valid image file",
                        "Ensure the image is not corrupted",
                        "Try taking a new photo of the document"
                    ],
                    fallback_available=True,
                    fallback_method="manual_entry"
                )
            
            # Check image size
            if image_data.size > 10_000_000:  # 10MB limit
                raise DocumentProcessingError(
                    message="Image file is too large",
                    severity=ErrorSeverity.LOW,
                    user_message="The image file is too large. Please use a smaller image.",
                    suggested_actions=[
                        "Compress the image before uploading",
                        "Take a photo at lower resolution"
                    ]
                )
            
            # Process with retry logic
            result = self._process_with_retry(image_data, document_type, user_profile)
            
            # Check quality and provide guidance
            quality_level = result.get("quality_level")
            if quality_level in [DocumentQuality.POOR, DocumentQuality.UNREADABLE]:
                result["warning"] = {
                    "message": error_message_generator.get_message("doc_poor_quality", language),
                    "severity": "medium",
                    "suggestedActions": result.get("improvement_suggestions", []),
                    "fallbackAvailable": True,
                    "fallbackMethod": "manual_review"
                }
                
                # Add to manual review queue if unreadable
                if quality_level == DocumentQuality.UNREADABLE:
                    self._queue_for_manual_review(result, user_profile)
                    result["requiresManualReview"] = True
            
            # Check validation results
            validation = result.get("validation_results", {})
            if not validation.get("is_valid"):
                result["warning"] = {
                    "message": error_message_generator.get_message("validation_failed", language),
                    "severity": "high",
                    "errors": validation.get("errors", []),
                    "suggestedActions": [
                        "Verify the document is authentic and not expired",
                        "Ensure all information is clearly visible",
                        "Contact support if you believe this is an error"
                    ]
                }
            
            result["success"] = True
            return result
        
        except DocumentProcessingError as e:
            logger.error(f"Document processing error: {str(e)}")
            return handle_error(e, {"documentType": document_type.value}, language)
        
        except Exception as e:
            logger.error(f"Unexpected error in document processing: {str(e)}")
            
            # Provide fallback option
            error_response = handle_error(e, {"documentType": document_type.value}, language)
            error_response["error"]["fallbackAvailable"] = True
            error_response["error"]["fallbackMethod"] = "manual_entry"
            error_response["error"]["suggestedActions"] = [
                "You can manually enter the document information",
                "Try uploading a different image",
                "Contact support for assistance"
            ]
            
            return error_response
    
    @with_retry(max_attempts=2, initial_delay=0.5)
    def _process_with_retry(
        self,
        image_data: np.ndarray,
        document_type: DocumentType,
        user_profile: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process document with retry logic for transient failures
        """
        return self.process_document(image_data, document_type, user_profile)
    
    def _queue_for_manual_review(
        self,
        document_result: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]]
    ):
        """
        Queue document for manual review when OCR fails
        
        Args:
            document_result: Processing result
            user_profile: User profile information
        """
        review_item = {
            "documentId": document_result.get("document_id"),
            "documentType": document_result.get("document_type"),
            "qualityScore": document_result.get("quality_score"),
            "userId": user_profile.get("profileId") if user_profile else None,
            "queuedAt": document_result.get("processed_at"),
            "reason": "unreadable_quality"
        }
        
        self.manual_review_queue.append(review_item)
        logger.info(f"Document {review_item['documentId']} queued for manual review")
    
    def get_manual_review_queue(self) -> list:
        """Get list of documents pending manual review"""
        return self.manual_review_queue
    
    def enable_fallback_mode(self):
        """Enable fallback mode for degraded operation"""
        self.fallback_mode = True
        logger.warning("Document processor entering fallback mode")
    
    def disable_fallback_mode(self):
        """Disable fallback mode"""
        self.fallback_mode = False
        logger.info("Document processor exiting fallback mode")
    
    def get_manual_entry_form(
        self,
        document_type: DocumentType
    ) -> Dict[str, Any]:
        """
        Get manual entry form as fallback when OCR fails
        
        Args:
            document_type: Type of document
            
        Returns:
            Form structure for manual data entry
        """
        forms = {
            DocumentType.AADHAAR: {
                "fields": [
                    {"name": "aadhaar_number", "label": "Aadhaar Number", "type": "text", "required": True},
                    {"name": "name", "label": "Name", "type": "text", "required": True},
                    {"name": "date_of_birth", "label": "Date of Birth", "type": "date", "required": True},
                    {"name": "gender", "label": "Gender", "type": "select", "options": ["male", "female", "other"], "required": True},
                    {"name": "address", "label": "Address", "type": "textarea", "required": False}
                ]
            },
            DocumentType.PAN: {
                "fields": [
                    {"name": "pan_number", "label": "PAN Number", "type": "text", "required": True},
                    {"name": "name", "label": "Name", "type": "text", "required": True},
                    {"name": "father_name", "label": "Father's Name", "type": "text", "required": False},
                    {"name": "date_of_birth", "label": "Date of Birth", "type": "date", "required": True}
                ]
            },
            DocumentType.BANK_PASSBOOK: {
                "fields": [
                    {"name": "account_number", "label": "Account Number", "type": "text", "required": True},
                    {"name": "ifsc_code", "label": "IFSC Code", "type": "text", "required": True},
                    {"name": "account_holder_name", "label": "Account Holder Name", "type": "text", "required": True},
                    {"name": "bank_name", "label": "Bank Name", "type": "text", "required": True}
                ]
            },
            DocumentType.LAND_RECORDS: {
                "fields": [
                    {"name": "survey_number", "label": "Survey Number", "type": "text", "required": True},
                    {"name": "land_area", "label": "Land Area", "type": "number", "required": True},
                    {"name": "land_unit", "label": "Unit", "type": "select", "options": ["acre", "hectare"], "required": True},
                    {"name": "owner_name", "label": "Owner Name", "type": "text", "required": True},
                    {"name": "village", "label": "Village", "type": "text", "required": True}
                ]
            },
            DocumentType.RATION_CARD: {
                "fields": [
                    {"name": "ration_card_number", "label": "Ration Card Number", "type": "text", "required": True},
                    {"name": "card_type", "label": "Card Type", "type": "select", "options": ["APL", "BPL", "AAY"], "required": True},
                    {"name": "head_of_family", "label": "Head of Family", "type": "text", "required": True},
                    {"name": "family_members", "label": "Number of Family Members", "type": "number", "required": True},
                    {"name": "address", "label": "Address", "type": "textarea", "required": False}
                ]
            },
            DocumentType.VOTER_ID: {
                "fields": [
                    {"name": "voter_id_number", "label": "Voter ID Number", "type": "text", "required": True},
                    {"name": "name", "label": "Name", "type": "text", "required": True},
                    {"name": "date_of_birth", "label": "Date of Birth", "type": "date", "required": True},
                    {"name": "gender", "label": "Gender", "type": "select", "options": ["male", "female", "other"], "required": True},
                    {"name": "address", "label": "Address", "type": "textarea", "required": False}
                ]
            }
        }
        
        return forms.get(document_type, {"fields": []})
