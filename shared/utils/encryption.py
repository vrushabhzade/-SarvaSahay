"""
Encryption utilities for sensitive data
Implements AES encryption for profile data and documents
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import os
from typing import Optional, Union
import json


class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption service with a key
        
        Args:
            encryption_key: Base64-encoded encryption key. If None, uses environment variable.
        """
        if encryption_key is None:
            encryption_key = os.getenv('ENCRYPTION_KEY', 'dev-encryption-key-change-in-production-32chars')
        
        # Derive a proper Fernet key from the encryption key
        self.key = self._derive_key(encryption_key)
        self.cipher = Fernet(self.key)
    
    def _derive_key(self, password: str) -> bytes:
        """
        Derive a Fernet-compatible key from a password using PBKDF2
        
        Args:
            password: Password or key string
            
        Returns:
            Base64-encoded 32-byte key suitable for Fernet
        """
        # Use a fixed salt for deterministic key derivation
        # In production, consider using a per-user salt stored separately
        salt = b'sarvasahay-platform-salt-2024'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, data: Union[str, dict]) -> str:
        """
        Encrypt data using AES encryption
        
        Args:
            data: String or dictionary to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        if isinstance(data, dict):
            data = json.dumps(data)
        
        if not isinstance(data, str):
            raise ValueError("Data must be a string or dictionary")
        
        encrypted_bytes = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_bytes).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data using AES encryption
        
        Args:
            encrypted_data: Base64-encoded encrypted string
            
        Returns:
            Decrypted string
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def encrypt_dict(self, data: dict) -> dict:
        """
        Encrypt all values in a dictionary
        
        Args:
            data: Dictionary with string values to encrypt
            
        Returns:
            Dictionary with encrypted values
        """
        encrypted = {}
        for key, value in data.items():
            if value is not None:
                encrypted[key] = self.encrypt(str(value))
            else:
                encrypted[key] = None
        return encrypted
    
    def decrypt_dict(self, encrypted_data: dict) -> dict:
        """
        Decrypt all values in a dictionary
        
        Args:
            encrypted_data: Dictionary with encrypted string values
            
        Returns:
            Dictionary with decrypted values
        """
        decrypted = {}
        for key, value in encrypted_data.items():
            if value is not None:
                decrypted[key] = self.decrypt(value)
            else:
                decrypted[key] = None
        return decrypted
    
    def mask_sensitive_data(self, data: str, visible_chars: int = 4) -> str:
        """
        Mask sensitive data for display purposes
        
        Args:
            data: Sensitive data string
            visible_chars: Number of characters to show at the end
            
        Returns:
            Masked string (e.g., "****5678")
        """
        if not data or len(data) <= visible_chars:
            return "****"
        
        return "*" * (len(data) - visible_chars) + data[-visible_chars:]


# Global encryption service instance
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """Get or create global encryption service instance"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


def encrypt_profile_data(profile_dict: dict) -> dict:
    """
    Encrypt sensitive fields in a user profile dictionary
    
    Args:
        profile_dict: User profile dictionary
        
    Returns:
        Profile dictionary with encrypted sensitive fields
    """
    service = get_encryption_service()
    
    # Create a copy to avoid modifying the original
    encrypted_profile = profile_dict.copy()
    
    # Encrypt documents section if present
    if 'documents' in encrypted_profile and encrypted_profile['documents']:
        encrypted_profile['documents'] = service.encrypt_dict(encrypted_profile['documents'])
    
    # Encrypt phone number in preferences if present
    if 'preferences' in encrypted_profile and encrypted_profile['preferences']:
        prefs = encrypted_profile['preferences']
        if 'phone_number' in prefs and prefs['phone_number']:
            prefs['phone_number'] = service.encrypt(prefs['phone_number'])
        if 'email' in prefs and prefs['email']:
            prefs['email'] = service.encrypt(prefs['email'])
    
    return encrypted_profile


def decrypt_profile_data(encrypted_profile: dict) -> dict:
    """
    Decrypt sensitive fields in an encrypted user profile dictionary
    
    Args:
        encrypted_profile: Encrypted user profile dictionary
        
    Returns:
        Profile dictionary with decrypted sensitive fields
    """
    service = get_encryption_service()
    
    # Create a copy to avoid modifying the original
    decrypted_profile = encrypted_profile.copy()
    
    # Decrypt documents section if present
    if 'documents' in decrypted_profile and decrypted_profile['documents']:
        decrypted_profile['documents'] = service.decrypt_dict(decrypted_profile['documents'])
    
    # Decrypt phone number in preferences if present
    if 'preferences' in decrypted_profile and decrypted_profile['preferences']:
        prefs = decrypted_profile['preferences']
        if 'phone_number' in prefs and prefs['phone_number']:
            prefs['phone_number'] = service.decrypt(prefs['phone_number'])
        if 'email' in prefs and prefs['email']:
            prefs['email'] = service.decrypt(prefs['email'])
    
    return decrypted_profile
