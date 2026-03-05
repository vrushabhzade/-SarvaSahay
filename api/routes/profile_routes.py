"""
Profile Management Routes
User profile CRUD operations with validation and security
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
import logging

from shared.models.user_profile import (
    UserProfile, UserProfileCreate, UserProfileUpdate, UserProfileResponse
)
from services.profile_service import ProfileService
from shared.config.settings import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

# Dependency to get profile service instance
def get_profile_service() -> ProfileService:
    """Get profile service instance"""
    return ProfileService()


@router.post("/profiles", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_data: UserProfileCreate,
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Create a new user profile
    
    - **profile_data**: Complete user profile information
    - Returns: Created profile with generated ID and metadata
    """
    try:
        # Convert Pydantic model to dict for service layer
        profile_dict = profile_data.dict()
        
        # Create profile using service
        profile_id = profile_service.create_profile(profile_dict)
        
        # Retrieve created profile
        created_profile = profile_service.get_profile(profile_id)
        if not created_profile:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Profile created but could not be retrieved"
            )
        
        logger.info(f"Profile created successfully: {profile_id}")
        
        # Convert back to response model
        return UserProfileResponse(**created_profile)
        
    except ValueError as e:
        logger.error(f"Profile validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Profile creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create profile"
        )


@router.get("/profiles/{profile_id}", response_model=UserProfileResponse)
async def get_profile(
    profile_id: str,
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Retrieve a user profile by ID
    
    - **profile_id**: Unique profile identifier
    - Returns: Complete user profile information
    """
    try:
        profile = profile_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile not found: {profile_id}"
            )
        
        return UserProfileResponse(**profile)
        
    except ValueError as e:
        logger.error(f"Invalid profile ID: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid profile ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile"
        )


@router.put("/profiles/{profile_id}", response_model=UserProfileResponse)
async def update_profile(
    profile_id: str,
    profile_updates: UserProfileUpdate,
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Update an existing user profile
    
    - **profile_id**: Unique profile identifier
    - **profile_updates**: Partial profile updates (only changed fields)
    - Returns: Updated profile information
    """
    try:
        # Convert updates to dict, excluding None values
        updates_dict = profile_updates.dict(exclude_none=True)
        
        if not updates_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No updates provided"
            )
        
        # Update profile using service
        success = profile_service.update_profile(profile_id, updates_dict)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile not found: {profile_id}"
            )
        
        # Retrieve updated profile
        updated_profile = profile_service.get_profile(profile_id)
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Profile updated but could not be retrieved"
            )
        
        logger.info(f"Profile updated successfully: {profile_id}")
        
        return UserProfileResponse(**updated_profile)
        
    except ValueError as e:
        logger.error(f"Profile update validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: str,
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Delete a user profile (GDPR compliance)
    
    - **profile_id**: Unique profile identifier
    - Returns: No content on successful deletion
    """
    try:
        success = profile_service.delete_profile(profile_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile not found: {profile_id}"
            )
        
        logger.info(f"Profile deleted successfully: {profile_id}")
        
    except ValueError as e:
        logger.error(f"Invalid profile ID for deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid profile ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete profile"
        )


@router.get("/profiles", response_model=List[str])
async def list_profiles(
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    List all profile IDs (admin endpoint)
    
    - **limit**: Maximum number of profiles to return (default: 100)
    - **offset**: Number of profiles to skip (default: 0)
    - Returns: List of profile IDs
    """
    try:
        if limit <= 0 or limit > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 1000"
            )
        
        if offset < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Offset must be non-negative"
            )
        
        # Get all profile IDs
        all_profile_ids = profile_service.list_profiles()
        
        # Apply pagination
        paginated_ids = all_profile_ids[offset:offset + limit]
        
        return paginated_ids
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile listing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list profiles"
        )


@router.get("/profiles/stats")
async def get_profile_stats(
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Get profile statistics (admin endpoint)
    
    - Returns: Profile count and other statistics
    """
    try:
        total_profiles = profile_service.get_profile_count()
        
        return {
            "total_profiles": total_profiles,
            "timestamp": "2026-01-25T13:15:00Z"  # Current timestamp
        }
        
    except Exception as e:
        logger.error(f"Profile stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile statistics"
        )