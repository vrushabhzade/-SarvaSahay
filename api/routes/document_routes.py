"""
Document Processing Routes
OCR-based document extraction and validation endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from typing import List
import logging

from services.document_processor import DocumentProcessor
from services.document_validator import DocumentValidator
from services.profile_service import ProfileService
from shared.config.settings import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


def get_document_processor() -> DocumentProcessor:
    """Get document processor instance"""
    return DocumentProcessor()


def get_document_validator() -> DocumentValidator:
    """Get document validator instance"""
    return DocumentValidator()


def get_profile_service() -> ProfileService:
    """Get profile service instance"""
    return ProfileService()


@router.post("/documents/upload/{user_id}")
async def upload_document(
    user_id: str,
    document_type: str,
    file: UploadFile = File(...),
    document_processor: DocumentProcessor = Depends(get_document_processor),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Upload and process a document
    
    - **user_id**: User profile identifier
    - **document_type**: Type of document (aadhaar, pan, land_records, bank_passbook)
    - **file**: Document image file
    - Returns: Processed document data with extracted information
    """
    try:
        # Verify user exists
        user_profile = profile_service.get_profile(user_id)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User profile not found: {user_id}"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Process document
        processed_doc = document_processor.process_document(file_content, document_type)
        
        logger.info(f"Document processed for user {user_id}: {document_type}")
        
        return {
            "user_id": user_id,
            "document_type": document_type,
            "extracted_data": processed_doc.get("extracted_data", {}),
            "quality_score": processed_doc.get("quality_score", 0),
            "validation_status": processed_doc.get("validation_status", "pending"),
            "suggestions": processed_doc.get("suggestions", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload error for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process document"
        )


@router.post("/documents/validate/{user_id}")
async def validate_document(
    user_id: str,
    document_type: str,
    extracted_data: dict,
    document_validator: DocumentValidator = Depends(get_document_validator),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Validate extracted document data against user profile
    
    - **user_id**: User profile identifier
    - **document_type**: Type of document
    - **extracted_data**: Data extracted from document
    - Returns: Validation results with inconsistencies flagged
    """
    try:
        # Get user profile
        user_profile = profile_service.get_profile(user_id)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User profile not found: {user_id}"
            )
        
        # Validate document
        validation_result = document_validator.validate_document(
            extracted_data,
            user_profile,
            document_type
        )
        
        logger.info(f"Document validated for user {user_id}: {document_type}")
        
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document validation error for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate document"
        )


@router.get("/documents/{user_id}")
async def get_user_documents(
    user_id: str,
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Get all processed documents for a user
    
    - **user_id**: User profile identifier
    - Returns: List of processed documents
    """
    try:
        # Verify user exists
        user_profile = profile_service.get_profile(user_id)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User profile not found: {user_id}"
            )
        
        # Get documents from profile
        documents = user_profile.get("documents", {})
        
        return {
            "user_id": user_id,
            "documents": documents
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document retrieval error for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )
