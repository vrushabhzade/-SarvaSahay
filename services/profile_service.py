"""
SarvaSahay Profile Service
User profile management with AES encryption and validation
"""

from typing import Dict, Any, Optional, List
import json
import hashlib
from datetime import datetime
from shared.utils.encryption import get_encryption_service, encrypt_profile_data, decrypt_profile_data


class ProfileService:
    """
    User profile management service
    Handles creation, updates, validation, and secure storage with AES encryption
    """
    
    def __init__(self):
        self.profiles = {}  # In-memory storage for demo
        self.encryption_service = get_encryption_service()
    
    def create_profile(self, profile_data: Dict[str, Any]) -> str:
        """Create new user profile with validation"""
        if not profile_data:
            raise ValueError("Profile data cannot be empty")
        
        # Validate required fields
        self._validate_profile_structure(profile_data)
        
        # Generate profile ID
        profile_id = self._generate_profile_id(profile_data)
        
        # Add metadata
        profile_data["profileId"] = profile_id
        profile_data["createdAt"] = datetime.utcnow().isoformat()
        profile_data["updatedAt"] = datetime.utcnow().isoformat()
        profile_data["version"] = 1
        
        # Store encrypted profile
        encrypted_profile = self._encrypt_profile(profile_data)
        self.profiles[profile_id] = encrypted_profile
        
        return profile_id
    
    def get_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user profile by ID"""
        if not profile_id:
            raise ValueError("Profile ID cannot be empty")
        
        encrypted_profile = self.profiles.get(profile_id)
        if not encrypted_profile:
            return None
        
        return self._decrypt_profile(encrypted_profile)
    
    def update_profile(self, profile_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing user profile"""
        if not profile_id or not updates:
            raise ValueError("Profile ID and updates cannot be empty")
        
        existing_profile = self.get_profile(profile_id)
        if not existing_profile:
            return False
        
        # Deep merge updates instead of overwriting entire sections
        for section, section_updates in updates.items():
            if section in existing_profile and isinstance(section_updates, dict):
                # Merge dictionaries for nested sections
                existing_profile[section].update(section_updates)
            else:
                # Direct assignment for non-dict values
                existing_profile[section] = section_updates
        
        existing_profile["updatedAt"] = datetime.utcnow().isoformat()
        existing_profile["version"] += 1
        
        # Validate updated profile
        self._validate_profile_structure(existing_profile)
        
        # Store updated profile
        encrypted_profile = self._encrypt_profile(existing_profile)
        self.profiles[profile_id] = encrypted_profile
        
        return True
    
    def delete_profile(self, profile_id: str) -> bool:
        """Delete user profile (GDPR compliance)"""
        if not profile_id:
            raise ValueError("Profile ID cannot be empty")
        
        if profile_id in self.profiles:
            del self.profiles[profile_id]
            return True
        
        return False
    
    def _validate_profile_structure(self, profile: Dict[str, Any]) -> None:
        """Validate profile has required structure"""
        required_sections = ["demographics", "economic", "location", "family"]
        
        for section in required_sections:
            if section not in profile:
                raise ValueError(f"Missing required section: {section}")
        
        # Validate demographics
        demo = profile["demographics"]
        required_demo_fields = ["age", "gender", "caste", "maritalStatus"]
        for field in required_demo_fields:
            if field not in demo:
                raise ValueError(f"Missing required demographics field: {field}")
        
        # Validate age range
        if not (0 <= demo["age"] <= 150):
            raise ValueError("Age must be between 0 and 150")
        
        # Validate economic data
        econ = profile["economic"]
        required_econ_fields = ["annualIncome", "landOwnership", "employmentStatus"]
        for field in required_econ_fields:
            if field not in econ:
                raise ValueError(f"Missing required economic field: {field}")
        
        # Validate income is non-negative
        if econ["annualIncome"] < 0:
            raise ValueError("Annual income cannot be negative")
        
        # Validate land ownership is non-negative
        if econ["landOwnership"] < 0:
            raise ValueError("Land ownership cannot be negative")
    
    def _generate_profile_id(self, profile_data: Dict[str, Any]) -> str:
        """Generate unique profile ID"""
        # Use hash of key profile data for uniqueness
        key_data = f"{profile_data['demographics']['age']}-{profile_data['location']['state']}-{datetime.utcnow().timestamp()}"
        return hashlib.md5(key_data.encode()).hexdigest()[:12]
    
    def _encrypt_profile(self, profile: Dict[str, Any]) -> str:
        """
        Encrypt profile data using AES encryption
        Encrypts sensitive fields including documents and contact information
        """
        # Encrypt sensitive fields
        encrypted_profile = encrypt_profile_data(profile)
        
        # Serialize to JSON
        profile_json = json.dumps(encrypted_profile, sort_keys=True)
        return profile_json
    
    def _decrypt_profile(self, encrypted_profile: str) -> Dict[str, Any]:
        """
        Decrypt profile data using AES encryption
        """
        # Deserialize from JSON
        profile = json.loads(encrypted_profile)
        
        # Decrypt sensitive fields
        decrypted_profile = decrypt_profile_data(profile)
        return decrypted_profile
    
    def get_profile_count(self) -> int:
        """Get total number of profiles"""
        return len(self.profiles)
    
    def list_profiles(self) -> List[str]:
        """List all profile IDs (for admin use)"""
        return list(self.profiles.keys())