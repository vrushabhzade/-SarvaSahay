"""
Unit tests for authentication service
Tests password hashing, MFA, and session management
"""

import pytest
from shared.utils.auth import (
    AuthenticationService,
    UserRole,
    MFAMethod,
    get_auth_service
)
import pyotp
import time


class TestPasswordHashing:
    """Test password hashing and verification"""
    
    def test_hash_password_generates_unique_hashes(self):
        """Test that same password with different salts produces different hashes"""
        service = AuthenticationService()
        password = "test_password_123"
        
        hash1, salt1 = service.hash_password(password)
        hash2, salt2 = service.hash_password(password)
        
        assert hash1 != hash2
        assert salt1 != salt2
    
    def test_hash_password_with_provided_salt(self):
        """Test password hashing with provided salt"""
        service = AuthenticationService()
        password = "test_password_123"
        salt = "fixed_salt_for_testing"
        
        hash1, returned_salt1 = service.hash_password(password, salt)
        hash2, returned_salt2 = service.hash_password(password, salt)
        
        assert hash1 == hash2
        assert returned_salt1 == returned_salt2 == salt
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        service = AuthenticationService()
        password = "correct_password"
        
        hashed, salt = service.hash_password(password)
        assert service.verify_password(password, hashed, salt) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        service = AuthenticationService()
        password = "correct_password"
        wrong_password = "wrong_password"
        
        hashed, salt = service.hash_password(password)
        assert service.verify_password(wrong_password, hashed, salt) is False


class TestUserManagement:
    """Test user creation and management"""
    
    def test_create_user_basic(self):
        """Test creating a basic user"""
        service = AuthenticationService()
        
        result = service.create_user(
            username="testuser",
            password="password123",
            role=UserRole.USER
        )
        
        assert result['username'] == "testuser"
        assert result['role'] == UserRole.USER.value
        assert result['mfa_enabled'] is False
        assert result['mfa_secret'] is None
    
    def test_create_admin_user_with_mfa(self):
        """Test creating admin user automatically enables MFA"""
        service = AuthenticationService()
        
        result = service.create_user(
            username="admin",
            password="admin_password",
            role=UserRole.ADMIN,
            email="admin@example.com"
        )
        
        assert result['username'] == "admin"
        assert result['role'] == UserRole.ADMIN.value
        assert result['mfa_enabled'] is True
        assert result['mfa_secret'] is not None
    
    def test_create_duplicate_user_raises_error(self):
        """Test that creating duplicate user raises error"""
        service = AuthenticationService()
        
        service.create_user(
            username="duplicate",
            password="password123",
            role=UserRole.USER
        )
        
        with pytest.raises(ValueError, match="already exists"):
            service.create_user(
                username="duplicate",
                password="password456",
                role=UserRole.USER
            )
    
    def test_create_operator_user_with_mfa(self):
        """Test creating operator user enables MFA"""
        service = AuthenticationService()
        
        result = service.create_user(
            username="operator",
            password="op_password",
            role=UserRole.OPERATOR
        )
        
        assert result['mfa_enabled'] is True
        assert result['mfa_secret'] is not None


class TestAuthentication:
    """Test authentication flows"""
    
    def test_authenticate_user_without_mfa(self):
        """Test successful authentication for user without MFA"""
        service = AuthenticationService()
        
        service.create_user(
            username="testuser",
            password="password123",
            role=UserRole.USER
        )
        
        result = service.authenticate("testuser", "password123")
        
        assert result['status'] == 'success'
        assert 'token' in result
        assert 'session_id' in result
        assert result['username'] == "testuser"
        assert result['role'] == UserRole.USER.value
    
    def test_authenticate_admin_requires_mfa(self):
        """Test that admin authentication requires MFA code"""
        service = AuthenticationService()
        
        service.create_user(
            username="admin",
            password="admin_pass",
            role=UserRole.ADMIN
        )
        
        result = service.authenticate("admin", "admin_pass")
        
        assert result['status'] == 'mfa_required'
        assert result['mfa_method'] == MFAMethod.TOTP.value
    
    def test_authenticate_admin_with_valid_mfa(self):
        """Test admin authentication with valid MFA code"""
        service = AuthenticationService()
        
        user_result = service.create_user(
            username="admin",
            password="admin_pass",
            role=UserRole.ADMIN
        )
        
        # Generate valid TOTP code
        totp = pyotp.TOTP(user_result['mfa_secret'])
        mfa_code = totp.now()
        
        result = service.authenticate("admin", "admin_pass", mfa_code)
        
        assert result['status'] == 'success'
        assert 'token' in result
        assert result['role'] == UserRole.ADMIN.value
    
    def test_authenticate_with_invalid_username(self):
        """Test authentication with invalid username"""
        service = AuthenticationService()
        
        with pytest.raises(ValueError, match="Invalid username or password"):
            service.authenticate("nonexistent", "password")
    
    def test_authenticate_with_invalid_password(self):
        """Test authentication with invalid password"""
        service = AuthenticationService()
        
        service.create_user(
            username="testuser",
            password="correct_password",
            role=UserRole.USER
        )
        
        with pytest.raises(ValueError, match="Invalid username or password"):
            service.authenticate("testuser", "wrong_password")
    
    def test_authenticate_with_invalid_mfa_code(self):
        """Test authentication with invalid MFA code"""
        service = AuthenticationService()
        
        service.create_user(
            username="admin",
            password="admin_pass",
            role=UserRole.ADMIN
        )
        
        with pytest.raises(ValueError, match="Invalid MFA code"):
            service.authenticate("admin", "admin_pass", "000000")


class TestAccountLocking:
    """Test account locking after failed attempts"""
    
    def test_account_locks_after_failed_attempts(self):
        """Test that account locks after 5 failed login attempts"""
        service = AuthenticationService()
        
        service.create_user(
            username="testuser",
            password="correct_password",
            role=UserRole.USER
        )
        
        # Attempt 5 failed logins
        for _ in range(5):
            try:
                service.authenticate("testuser", "wrong_password")
            except ValueError:
                pass
        
        # Next attempt should indicate locked account
        with pytest.raises(ValueError, match="Account is locked"):
            service.authenticate("testuser", "correct_password")
    
    def test_unlock_account_by_admin(self):
        """Test that admin can unlock locked account"""
        service = AuthenticationService()
        
        # Create admin and regular user
        service.create_user(
            username="admin",
            password="admin_pass",
            role=UserRole.ADMIN
        )
        
        service.create_user(
            username="testuser",
            password="correct_password",
            role=UserRole.USER
        )
        
        # Lock the account
        for _ in range(5):
            try:
                service.authenticate("testuser", "wrong_password")
            except ValueError:
                pass
        
        # Admin unlocks account
        result = service.unlock_account("testuser", "admin")
        assert result is True
        
        # User can now login
        auth_result = service.authenticate("testuser", "correct_password")
        assert auth_result['status'] == 'success'
    
    def test_non_admin_cannot_unlock_account(self):
        """Test that non-admin cannot unlock accounts"""
        service = AuthenticationService()
        
        service.create_user(
            username="user1",
            password="password1",
            role=UserRole.USER
        )
        
        service.create_user(
            username="user2",
            password="password2",
            role=UserRole.USER
        )
        
        with pytest.raises(ValueError, match="Insufficient permissions"):
            service.unlock_account("user2", "user1")


class TestMFA:
    """Test multi-factor authentication"""
    
    def test_verify_valid_mfa_code(self):
        """Test verification of valid MFA code"""
        service = AuthenticationService()
        
        result = service.create_user(
            username="admin",
            password="password",
            role=UserRole.ADMIN
        )
        
        # Generate valid code
        totp = pyotp.TOTP(result['mfa_secret'])
        code = totp.now()
        
        assert service.verify_mfa_code("admin", code) is True
    
    def test_verify_invalid_mfa_code(self):
        """Test verification of invalid MFA code"""
        service = AuthenticationService()
        
        service.create_user(
            username="admin",
            password="password",
            role=UserRole.ADMIN
        )
        
        assert service.verify_mfa_code("admin", "000000") is False
    
    def test_get_mfa_qr_code_uri(self):
        """Test getting QR code URI for MFA setup"""
        service = AuthenticationService()
        
        service.create_user(
            username="admin",
            password="password",
            role=UserRole.ADMIN
        )
        
        uri = service.get_mfa_qr_code_uri("admin")
        
        assert "otpauth://totp/" in uri
        assert "admin" in uri
        assert "SarvaSahay" in uri
    
    def test_mfa_qr_code_for_non_mfa_user_raises_error(self):
        """Test that getting QR code for non-MFA user raises error"""
        service = AuthenticationService()
        
        service.create_user(
            username="user",
            password="password",
            role=UserRole.USER
        )
        
        with pytest.raises(ValueError, match="MFA not enabled"):
            service.get_mfa_qr_code_uri("user")


class TestTokenManagement:
    """Test JWT token generation and verification"""
    
    def test_generate_and_verify_token(self):
        """Test token generation and verification"""
        service = AuthenticationService()
        
        service.create_user(
            username="testuser",
            password="password",
            role=UserRole.USER
        )
        
        auth_result = service.authenticate("testuser", "password")
        token = auth_result['token']
        
        payload = service.verify_token(token)
        
        assert payload['username'] == "testuser"
        assert payload['role'] == UserRole.USER.value
        assert 'iat' in payload
        assert 'exp' in payload
    
    def test_verify_invalid_token(self):
        """Test verification of invalid token"""
        service = AuthenticationService()
        
        with pytest.raises(ValueError, match="Invalid token"):
            service.verify_token("invalid.token.here")
    
    def test_require_role_admin(self):
        """Test role requirement check for admin"""
        service = AuthenticationService()
        
        service.create_user(
            username="admin",
            password="password",
            role=UserRole.ADMIN
        )
        
        # Admin without MFA for testing
        service.users["admin"]["mfa_enabled"] = False
        
        auth_result = service.authenticate("admin", "password")
        token = auth_result['token']
        
        # Admin should have access to admin role
        assert service.require_role(token, UserRole.ADMIN) is True
        
        # Admin should have access to user role
        assert service.require_role(token, UserRole.USER) is True
    
    def test_require_role_user_denied(self):
        """Test that user cannot access admin role"""
        service = AuthenticationService()
        
        service.create_user(
            username="user",
            password="password",
            role=UserRole.USER
        )
        
        auth_result = service.authenticate("user", "password")
        token = auth_result['token']
        
        # User should not have access to admin role
        assert service.require_role(token, UserRole.ADMIN) is False


class TestSessionManagement:
    """Test session management"""
    
    def test_verify_valid_session(self):
        """Test verification of valid session"""
        service = AuthenticationService()
        
        service.create_user(
            username="testuser",
            password="password",
            role=UserRole.USER
        )
        
        auth_result = service.authenticate("testuser", "password")
        session_id = auth_result['session_id']
        
        session = service.verify_session(session_id)
        
        assert session['username'] == "testuser"
        assert session['role'] == UserRole.USER.value
    
    def test_verify_invalid_session(self):
        """Test verification of invalid session"""
        service = AuthenticationService()
        
        with pytest.raises(ValueError, match="Invalid session"):
            service.verify_session("invalid_session_id")
    
    def test_logout_invalidates_session(self):
        """Test that logout invalidates session"""
        service = AuthenticationService()
        
        service.create_user(
            username="testuser",
            password="password",
            role=UserRole.USER
        )
        
        auth_result = service.authenticate("testuser", "password")
        session_id = auth_result['session_id']
        
        # Logout
        assert service.logout(session_id) is True
        
        # Session should be invalid
        with pytest.raises(ValueError, match="Invalid session"):
            service.verify_session(session_id)


class TestPasswordChange:
    """Test password change functionality"""
    
    def test_change_password_success(self):
        """Test successful password change"""
        service = AuthenticationService()
        
        service.create_user(
            username="testuser",
            password="old_password",
            role=UserRole.USER
        )
        
        # Change password
        result = service.change_password(
            "testuser",
            "old_password",
            "new_password"
        )
        
        assert result is True
        
        # Old password should not work
        with pytest.raises(ValueError):
            service.authenticate("testuser", "old_password")
        
        # New password should work
        auth_result = service.authenticate("testuser", "new_password")
        assert auth_result['status'] == 'success'
    
    def test_change_password_wrong_old_password(self):
        """Test password change with wrong old password"""
        service = AuthenticationService()
        
        service.create_user(
            username="testuser",
            password="correct_password",
            role=UserRole.USER
        )
        
        with pytest.raises(ValueError, match="Invalid current password"):
            service.change_password(
                "testuser",
                "wrong_old_password",
                "new_password"
            )


class TestGlobalService:
    """Test global service instance"""
    
    def test_get_auth_service_singleton(self):
        """Test that get_auth_service returns singleton instance"""
        service1 = get_auth_service()
        service2 = get_auth_service()
        
        assert service1 is service2
