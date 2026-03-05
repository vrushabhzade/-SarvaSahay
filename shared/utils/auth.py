"""
Authentication and Authorization utilities
Implements multi-factor authentication for admin access
"""

import hashlib
import secrets
import time
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import pyotp
import jwt


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    OPERATOR = "operator"
    USER = "user"
    READONLY = "readonly"


class MFAMethod(str, Enum):
    """Multi-factor authentication methods"""
    TOTP = "totp"  # Time-based One-Time Password
    SMS = "sms"    # SMS-based OTP
    EMAIL = "email"  # Email-based OTP


class AuthenticationService:
    """
    Authentication service with multi-factor authentication support
    Implements secure password hashing and MFA for admin access
    """
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize authentication service
        
        Args:
            secret_key: Secret key for JWT token generation
        """
        import os
        self.secret_key = secret_key or os.getenv(
            'AUTH_SECRET_KEY', 
            'dev-secret-key-change-in-production'
        )
        self.token_expiry_hours = 24
        self.mfa_required_roles = {UserRole.ADMIN, UserRole.OPERATOR}
        
        # In-memory storage for demo (use database in production)
        self.users = {}
        self.mfa_secrets = {}
        self.active_sessions = {}
        self.failed_attempts = {}
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """
        Hash password using PBKDF2 with SHA-256
        
        Args:
            password: Plain text password
            salt: Optional salt (generated if not provided)
            
        Returns:
            Tuple of (hashed_password, salt)
        """
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Use PBKDF2 with 100,000 iterations
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        
        return hashed.hex(), salt
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """
        Verify password against stored hash
        
        Args:
            password: Plain text password to verify
            hashed_password: Stored password hash
            salt: Salt used for hashing
            
        Returns:
            True if password matches, False otherwise
        """
        computed_hash, _ = self.hash_password(password, salt)
        return secrets.compare_digest(computed_hash, hashed_password)
    
    def create_user(
        self, 
        username: str, 
        password: str, 
        role: UserRole,
        email: Optional[str] = None,
        phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create new user with hashed password
        
        Args:
            username: Unique username
            password: Plain text password
            role: User role
            email: Optional email for MFA
            phone: Optional phone for MFA
            
        Returns:
            User information dictionary
        """
        if username in self.users:
            raise ValueError(f"User {username} already exists")
        
        # Hash password
        hashed_password, salt = self.hash_password(password)
        
        # Create user record
        user = {
            'username': username,
            'password_hash': hashed_password,
            'salt': salt,
            'role': role.value,
            'email': email,
            'phone': phone,
            'mfa_enabled': role in self.mfa_required_roles,
            'created_at': datetime.utcnow().isoformat(),
            'last_login': None,
            'is_locked': False
        }
        
        self.users[username] = user
        
        # Generate MFA secret if required
        if user['mfa_enabled']:
            self.mfa_secrets[username] = pyotp.random_base32()
        
        return {
            'username': username,
            'role': role.value,
            'mfa_enabled': user['mfa_enabled'],
            'mfa_secret': self.mfa_secrets.get(username) if user['mfa_enabled'] else None
        }
    
    def authenticate(
        self, 
        username: str, 
        password: str,
        mfa_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Authenticate user with password and optional MFA
        
        Args:
            username: Username
            password: Plain text password
            mfa_code: Optional MFA code for two-factor authentication
            
        Returns:
            Authentication result with token if successful
        """
        # Check if user exists
        if username not in self.users:
            self._record_failed_attempt(username)
            raise ValueError("Invalid username or password")
        
        user = self.users[username]
        
        # Check if account is locked
        if user['is_locked']:
            raise ValueError("Account is locked due to too many failed attempts")
        
        # Verify password
        if not self.verify_password(password, user['password_hash'], user['salt']):
            self._record_failed_attempt(username)
            raise ValueError("Invalid username or password")
        
        # Check MFA if enabled
        if user['mfa_enabled']:
            if not mfa_code:
                return {
                    'status': 'mfa_required',
                    'message': 'Multi-factor authentication code required',
                    'mfa_method': MFAMethod.TOTP.value
                }
            
            if not self.verify_mfa_code(username, mfa_code):
                self._record_failed_attempt(username)
                raise ValueError("Invalid MFA code")
        
        # Clear failed attempts on successful login
        self.failed_attempts.pop(username, None)
        
        # Update last login
        user['last_login'] = datetime.utcnow().isoformat()
        
        # Generate JWT token
        token = self._generate_token(username, user['role'])
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        self.active_sessions[session_id] = {
            'username': username,
            'role': user['role'],
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(hours=self.token_expiry_hours)
        }
        
        return {
            'status': 'success',
            'token': token,
            'session_id': session_id,
            'username': username,
            'role': user['role'],
            'expires_in': self.token_expiry_hours * 3600
        }
    
    def verify_mfa_code(self, username: str, code: str) -> bool:
        """
        Verify TOTP MFA code
        
        Args:
            username: Username
            code: 6-digit TOTP code
            
        Returns:
            True if code is valid, False otherwise
        """
        if username not in self.mfa_secrets:
            return False
        
        totp = pyotp.TOTP(self.mfa_secrets[username])
        return totp.verify(code, valid_window=1)  # Allow 30 second window
    
    def get_mfa_qr_code_uri(self, username: str, issuer: str = "SarvaSahay") -> str:
        """
        Get QR code URI for TOTP setup
        
        Args:
            username: Username
            issuer: Application name
            
        Returns:
            OTP Auth URI for QR code generation
        """
        if username not in self.mfa_secrets:
            raise ValueError(f"MFA not enabled for user {username}")
        
        totp = pyotp.TOTP(self.mfa_secrets[username])
        return totp.provisioning_uri(name=username, issuer_name=issuer)
    
    def _generate_token(self, username: str, role: str) -> str:
        """
        Generate JWT token for authenticated user
        
        Args:
            username: Username
            role: User role
            
        Returns:
            JWT token string
        """
        payload = {
            'username': username,
            'role': role,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiry_hours)
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        return token
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
    
    def verify_session(self, session_id: str) -> Dict[str, Any]:
        """
        Verify active session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session information
        """
        if session_id not in self.active_sessions:
            raise ValueError("Invalid session")
        
        session = self.active_sessions[session_id]
        
        # Check if session has expired
        if datetime.utcnow() > session['expires_at']:
            del self.active_sessions[session_id]
            raise ValueError("Session has expired")
        
        return session
    
    def logout(self, session_id: str) -> bool:
        """
        Logout user and invalidate session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if logout successful
        """
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False
    
    def _record_failed_attempt(self, username: str) -> None:
        """
        Record failed login attempt and lock account if threshold exceeded
        
        Args:
            username: Username
        """
        if username not in self.failed_attempts:
            self.failed_attempts[username] = {
                'count': 0,
                'first_attempt': time.time()
            }
        
        attempt_data = self.failed_attempts[username]
        attempt_data['count'] += 1
        
        # Lock account after 5 failed attempts within 15 minutes
        if attempt_data['count'] >= 5:
            time_window = time.time() - attempt_data['first_attempt']
            if time_window < 900:  # 15 minutes
                if username in self.users:
                    self.users[username]['is_locked'] = True
    
    def unlock_account(self, username: str, admin_username: str) -> bool:
        """
        Unlock user account (admin only)
        
        Args:
            username: Username to unlock
            admin_username: Admin performing the unlock
            
        Returns:
            True if unlock successful
        """
        # Verify admin has permission
        if admin_username not in self.users:
            raise ValueError("Admin user not found")
        
        admin = self.users[admin_username]
        if admin['role'] != UserRole.ADMIN.value:
            raise ValueError("Insufficient permissions")
        
        # Unlock account
        if username in self.users:
            self.users[username]['is_locked'] = False
            self.failed_attempts.pop(username, None)
            return True
        
        return False
    
    def change_password(
        self, 
        username: str, 
        old_password: str, 
        new_password: str
    ) -> bool:
        """
        Change user password
        
        Args:
            username: Username
            old_password: Current password
            new_password: New password
            
        Returns:
            True if password changed successfully
        """
        if username not in self.users:
            raise ValueError("User not found")
        
        user = self.users[username]
        
        # Verify old password
        if not self.verify_password(old_password, user['password_hash'], user['salt']):
            raise ValueError("Invalid current password")
        
        # Hash new password
        hashed_password, salt = self.hash_password(new_password)
        
        # Update user record
        user['password_hash'] = hashed_password
        user['salt'] = salt
        
        return True
    
    def require_role(self, token: str, required_role: UserRole) -> bool:
        """
        Check if token has required role
        
        Args:
            token: JWT token
            required_role: Required role
            
        Returns:
            True if user has required role
        """
        payload = self.verify_token(token)
        user_role = payload.get('role')
        
        # Admin has access to everything
        if user_role == UserRole.ADMIN.value:
            return True
        
        # Check specific role
        return user_role == required_role.value


# Global authentication service instance
_auth_service: Optional[AuthenticationService] = None


def get_auth_service() -> AuthenticationService:
    """Get or create global authentication service instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthenticationService()
    return _auth_service
