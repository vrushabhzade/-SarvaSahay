"""
Unit Tests for Profile Service
Tests user profile management functionality
"""

import pytest
from typing import Dict, Any
from services.profile_service import ProfileService


class TestProfileService:
    """Test cases for the Profile Service"""
    
    def test_service_initialization(self):
        """Test that the profile service initializes correctly"""
        service = ProfileService()
        assert service.get_profile_count() == 0
        assert service.encryption_key is not None
    
    def test_create_profile_success(self, sample_user_profile):
        """Test successful profile creation"""
        service = ProfileService()
        
        profile_id = service.create_profile(sample_user_profile)
        
        assert profile_id is not None
        assert len(profile_id) == 12  # MD5 hash truncated to 12 chars
        assert service.get_profile_count() == 1
    
    def test_create_profile_empty_data(self):
        """Test profile creation with empty data"""
        service = ProfileService()
        
        with pytest.raises(ValueError, match="Profile data cannot be empty"):
            service.create_profile({})
    
    def test_create_profile_missing_sections(self):
        """Test profile creation with missing required sections"""
        service = ProfileService()
        
        incomplete_profile = {
            "demographics": {"age": 30, "gender": "male", "caste": "General", "maritalStatus": "single"}
            # Missing economic, location, family sections
        }
        
        with pytest.raises(ValueError, match="Missing required section"):
            service.create_profile(incomplete_profile)
    
    def test_create_profile_invalid_age(self, sample_user_profile):
        """Test profile creation with invalid age"""
        service = ProfileService()
        
        sample_user_profile["demographics"]["age"] = -5  # Invalid age
        
        with pytest.raises(ValueError, match="Age must be between 0 and 150"):
            service.create_profile(sample_user_profile)
    
    def test_create_profile_negative_income(self, sample_user_profile):
        """Test profile creation with negative income"""
        service = ProfileService()
        
        sample_user_profile["economic"]["annualIncome"] = -1000  # Invalid income
        
        with pytest.raises(ValueError, match="Annual income cannot be negative"):
            service.create_profile(sample_user_profile)
    
    def test_get_profile_success(self, sample_user_profile):
        """Test successful profile retrieval"""
        service = ProfileService()
        
        profile_id = service.create_profile(sample_user_profile)
        retrieved_profile = service.get_profile(profile_id)
        
        assert retrieved_profile is not None
        assert retrieved_profile["profileId"] == profile_id
        assert retrieved_profile["demographics"]["age"] == sample_user_profile["demographics"]["age"]
        assert "createdAt" in retrieved_profile
        assert "updatedAt" in retrieved_profile
        assert retrieved_profile["version"] == 1
    
    def test_get_profile_not_found(self):
        """Test profile retrieval with non-existent ID"""
        service = ProfileService()
        
        retrieved_profile = service.get_profile("non-existent-id")
        
        assert retrieved_profile is None
    
    def test_get_profile_empty_id(self):
        """Test profile retrieval with empty ID"""
        service = ProfileService()
        
        with pytest.raises(ValueError, match="Profile ID cannot be empty"):
            service.get_profile("")
    
    def test_update_profile_success(self, sample_user_profile):
        """Test successful profile update"""
        service = ProfileService()
        
        profile_id = service.create_profile(sample_user_profile)
        
        updates = {
            "demographics": {"age": 36},  # Update age
            "economic": {"annualIncome": 130000}  # Update income
        }
        
        success = service.update_profile(profile_id, updates)
        
        assert success is True
        
        updated_profile = service.get_profile(profile_id)
        assert updated_profile["demographics"]["age"] == 36
        assert updated_profile["economic"]["annualIncome"] == 130000
        assert updated_profile["version"] == 2  # Version incremented
    
    def test_update_profile_not_found(self):
        """Test profile update with non-existent ID"""
        service = ProfileService()
        
        success = service.update_profile("non-existent-id", {"demographics": {"age": 30}})
        
        assert success is False
    
    def test_update_profile_empty_params(self):
        """Test profile update with empty parameters"""
        service = ProfileService()
        
        with pytest.raises(ValueError, match="Profile ID and updates cannot be empty"):
            service.update_profile("", {})
        
        with pytest.raises(ValueError, match="Profile ID and updates cannot be empty"):
            service.update_profile("some-id", {})
    
    def test_delete_profile_success(self, sample_user_profile):
        """Test successful profile deletion (GDPR compliance)"""
        service = ProfileService()
        
        profile_id = service.create_profile(sample_user_profile)
        assert service.get_profile_count() == 1
        
        success = service.delete_profile(profile_id)
        
        assert success is True
        assert service.get_profile_count() == 0
        assert service.get_profile(profile_id) is None
    
    def test_delete_profile_not_found(self):
        """Test profile deletion with non-existent ID"""
        service = ProfileService()
        
        success = service.delete_profile("non-existent-id")
        
        assert success is False
    
    def test_delete_profile_empty_id(self):
        """Test profile deletion with empty ID"""
        service = ProfileService()
        
        with pytest.raises(ValueError, match="Profile ID cannot be empty"):
            service.delete_profile("")
    
    def test_list_profiles(self, sample_user_profile):
        """Test listing all profile IDs"""
        service = ProfileService()
        
        # Create multiple profiles
        profile_id1 = service.create_profile(sample_user_profile)
        
        # Create second profile with different data
        profile2 = sample_user_profile.copy()
        profile2["demographics"]["age"] = 40
        profile_id2 = service.create_profile(profile2)
        
        profile_ids = service.list_profiles()
        
        assert len(profile_ids) == 2
        assert profile_id1 in profile_ids
        assert profile_id2 in profile_ids
    
    def test_profile_versioning(self, sample_user_profile):
        """Test profile versioning on updates"""
        service = ProfileService()
        
        profile_id = service.create_profile(sample_user_profile)
        original_profile = service.get_profile(profile_id)
        assert original_profile["version"] == 1
        
        # First update
        service.update_profile(profile_id, {"demographics": {"age": 36}})
        updated_profile = service.get_profile(profile_id)
        assert updated_profile["version"] == 2
        
        # Second update
        service.update_profile(profile_id, {"economic": {"annualIncome": 140000}})
        final_profile = service.get_profile(profile_id)
        assert final_profile["version"] == 3
    
    def test_profile_timestamps(self, sample_user_profile):
        """Test profile creation and update timestamps"""
        service = ProfileService()
        
        profile_id = service.create_profile(sample_user_profile)
        original_profile = service.get_profile(profile_id)
        
        assert "createdAt" in original_profile
        assert "updatedAt" in original_profile
        
        original_updated_at = original_profile["updatedAt"]
        
        # Update profile
        service.update_profile(profile_id, {"demographics": {"age": 36}})
        updated_profile = service.get_profile(profile_id)
        
        # updatedAt should change, createdAt should remain the same
        assert updated_profile["createdAt"] == original_profile["createdAt"]
        assert updated_profile["updatedAt"] != original_updated_at