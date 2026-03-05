"""
Serialization utilities for data models
Handles JSON serialization/deserialization with encryption support
"""

import json
from typing import Any, Dict, Optional, Type, TypeVar
from datetime import datetime
from pydantic import BaseModel
from .encryption import encrypt_profile_data, decrypt_profile_data, get_encryption_service

T = TypeVar('T', bound=BaseModel)


class ModelSerializer:
    """Serializer for Pydantic models with encryption support"""
    
    @staticmethod
    def serialize(model: BaseModel, encrypt_sensitive: bool = True) -> str:
        """
        Serialize a Pydantic model to JSON string
        
        Args:
            model: Pydantic model instance
            encrypt_sensitive: Whether to encrypt sensitive fields
            
        Returns:
            JSON string representation
        """
        model_dict = model.dict()
        
        # Encrypt sensitive data if requested
        if encrypt_sensitive and hasattr(model, '__class__') and model.__class__.__name__ == 'UserProfile':
            model_dict = encrypt_profile_data(model_dict)
        
        return json.dumps(model_dict, default=str)
    
    @staticmethod
    def deserialize(data: str, model_class: Type[T], decrypt_sensitive: bool = True) -> T:
        """
        Deserialize JSON string to a Pydantic model
        
        Args:
            data: JSON string
            model_class: Pydantic model class
            decrypt_sensitive: Whether to decrypt sensitive fields
            
        Returns:
            Model instance
        """
        model_dict = json.loads(data)
        
        # Decrypt sensitive data if requested
        if decrypt_sensitive and model_class.__name__ == 'UserProfile':
            model_dict = decrypt_profile_data(model_dict)
        
        return model_class(**model_dict)
    
    @staticmethod
    def to_dict(model: BaseModel, encrypt_sensitive: bool = False, 
                exclude_none: bool = False) -> Dict[str, Any]:
        """
        Convert Pydantic model to dictionary
        
        Args:
            model: Pydantic model instance
            encrypt_sensitive: Whether to encrypt sensitive fields
            exclude_none: Whether to exclude None values
            
        Returns:
            Dictionary representation
        """
        model_dict = model.dict(exclude_none=exclude_none)
        
        # Encrypt sensitive data if requested
        if encrypt_sensitive and hasattr(model, '__class__') and model.__class__.__name__ == 'UserProfile':
            model_dict = encrypt_profile_data(model_dict)
        
        return model_dict
    
    @staticmethod
    def from_dict(data: Dict[str, Any], model_class: Type[T], 
                  decrypt_sensitive: bool = False) -> T:
        """
        Create Pydantic model from dictionary
        
        Args:
            data: Dictionary data
            model_class: Pydantic model class
            decrypt_sensitive: Whether to decrypt sensitive fields
            
        Returns:
            Model instance
        """
        # Decrypt sensitive data if requested
        if decrypt_sensitive and model_class.__name__ == 'UserProfile':
            data = decrypt_profile_data(data)
        
        return model_class(**data)


class SecureSerializer:
    """Serializer with automatic encryption for sensitive models"""
    
    SENSITIVE_MODELS = ['UserProfile', 'Documents', 'Application']
    
    @classmethod
    def is_sensitive_model(cls, model: BaseModel) -> bool:
        """Check if a model contains sensitive data"""
        return model.__class__.__name__ in cls.SENSITIVE_MODELS
    
    @classmethod
    def serialize_secure(cls, model: BaseModel) -> str:
        """
        Serialize model with automatic encryption for sensitive data
        
        Args:
            model: Pydantic model instance
            
        Returns:
            JSON string with encrypted sensitive fields
        """
        encrypt = cls.is_sensitive_model(model)
        return ModelSerializer.serialize(model, encrypt_sensitive=encrypt)
    
    @classmethod
    def deserialize_secure(cls, data: str, model_class: Type[T]) -> T:
        """
        Deserialize model with automatic decryption for sensitive data
        
        Args:
            data: JSON string
            model_class: Pydantic model class
            
        Returns:
            Model instance with decrypted sensitive fields
        """
        decrypt = model_class.__name__ in cls.SENSITIVE_MODELS
        return ModelSerializer.deserialize(data, model_class, decrypt_sensitive=decrypt)


def mask_sensitive_fields(model_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mask sensitive fields in a model dictionary for safe display
    
    Args:
        model_dict: Dictionary representation of a model
        
    Returns:
        Dictionary with masked sensitive fields
    """
    service = get_encryption_service()
    masked = model_dict.copy()
    
    # Mask document fields
    if 'documents' in masked and masked['documents']:
        docs = masked['documents']
        if 'aadhaar' in docs and docs['aadhaar']:
            docs['aadhaar'] = service.mask_sensitive_data(docs['aadhaar'], 4)
        if 'pan' in docs and docs['pan']:
            docs['pan'] = service.mask_sensitive_data(docs['pan'], 4)
        if 'bank_account' in docs and docs['bank_account']:
            docs['bank_account'] = service.mask_sensitive_data(docs['bank_account'], 4)
    
    # Mask phone number
    if 'preferences' in masked and masked['preferences']:
        prefs = masked['preferences']
        if 'phone_number' in prefs and prefs['phone_number']:
            prefs['phone_number'] = service.mask_sensitive_data(prefs['phone_number'], 4)
        if 'email' in prefs and prefs['email']:
            # Mask email keeping domain visible
            email = prefs['email']
            if '@' in email:
                local, domain = email.split('@', 1)
                prefs['email'] = service.mask_sensitive_data(local, 2) + '@' + domain
    
    return masked


def validate_and_sanitize(data: Dict[str, Any], model_class: Type[T]) -> T:
    """
    Validate and sanitize input data before creating a model
    
    Args:
        data: Input dictionary
        model_class: Pydantic model class
        
    Returns:
        Validated and sanitized model instance
        
    Raises:
        ValueError: If validation fails
    """
    try:
        # Pydantic will handle validation
        model = model_class(**data)
        return model
    except Exception as e:
        raise ValueError(f"Validation failed: {str(e)}")


# Convenience functions for common operations

def serialize_profile(profile: BaseModel, secure: bool = True) -> str:
    """Serialize user profile with optional encryption"""
    if secure:
        return SecureSerializer.serialize_secure(profile)
    return ModelSerializer.serialize(profile, encrypt_sensitive=False)


def deserialize_profile(data: str, model_class: Type[T], secure: bool = True) -> T:
    """Deserialize user profile with optional decryption"""
    if secure:
        return SecureSerializer.deserialize_secure(data, model_class)
    return ModelSerializer.deserialize(data, model_class, decrypt_sensitive=False)


def profile_to_dict(profile: BaseModel, mask_sensitive: bool = False, 
                   encrypt: bool = False) -> Dict[str, Any]:
    """
    Convert profile to dictionary with optional masking or encryption
    
    Args:
        profile: Profile model instance
        mask_sensitive: Whether to mask sensitive fields for display
        encrypt: Whether to encrypt sensitive fields
        
    Returns:
        Dictionary representation
    """
    profile_dict = ModelSerializer.to_dict(profile, encrypt_sensitive=encrypt)
    
    if mask_sensitive:
        profile_dict = mask_sensitive_fields(profile_dict)
    
    return profile_dict
