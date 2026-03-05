"""
Unit tests for SMS Interface Handler
Tests menu-driven navigation and multi-language support
"""

import pytest
from services.sms_interface import SMSInterfaceHandler, SMSLanguage, SMSMenuState


class TestSMSInterfaceHandler:
    """Test SMS interface handler functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.handler = SMSInterfaceHandler()
    
    def test_initial_contact_shows_language_menu(self):
        """Test that initial contact shows language selection"""
        response = self.handler.process_sms("+919876543210", "HELLO")
        
        assert "Welcome to SarvaSahay" in response
        assert "Select Language" in response
        assert "हिंदी" in response
        assert "मराठी" in response
    
    def test_language_selection_hindi(self):
        """Test selecting Hindi language"""
        phone = "+919876543210"
        
        # Initial contact
        self.handler.process_sms(phone, "HELLO")
        
        # Select Hindi (option 1)
        response = self.handler.process_sms(phone, "1")
        
        assert "सर्वसहाय" in response
        assert "प्रोफाइल बनाएं" in response
    
    def test_language_selection_marathi(self):
        """Test selecting Marathi language"""
        phone = "+919876543211"
        
        # Initial contact
        self.handler.process_sms(phone, "HELLO")
        
        # Select Marathi (option 2)
        response = self.handler.process_sms(phone, "2")
        
        assert "सर्वसहाय" in response
        assert "प्रोफाईल तयार करा" in response
    
    def test_language_selection_english(self):
        """Test selecting English language"""
        phone = "+919876543212"
        
        # Initial contact
        self.handler.process_sms(phone, "HELLO")
        
        # Select English (option 3)
        response = self.handler.process_sms(phone, "3")
        
        assert "SarvaSahay Main Menu" in response
        assert "Create Profile" in response
    
    def test_profile_creation_command(self):
        """Test profile creation command"""
        phone = "+919876543213"
        
        response = self.handler.process_sms(phone, "PROFILE BANAO")
        
        assert "age" in response.lower() or "उम्र" in response
    
    def test_profile_creation_workflow_age(self):
        """Test profile creation - age input"""
        phone = "+919876543214"
        
        # Start profile creation
        self.handler.process_sms(phone, "PROFILE BANAO")
        
        # Enter age
        response = self.handler.process_sms(phone, "35")
        
        assert "gender" in response.lower() or "लिंग" in response
    
    def test_profile_creation_workflow_gender(self):
        """Test profile creation - gender input"""
        phone = "+919876543215"
        
        # Start and enter age
        self.handler.process_sms(phone, "PROFILE BANAO")
        self.handler.process_sms(phone, "35")
        
        # Enter gender (1 = male)
        response = self.handler.process_sms(phone, "1")
        
        assert "category" in response.lower() or "श्रेणी" in response or "caste" in response.lower()
    
    def test_profile_creation_workflow_caste(self):
        """Test profile creation - caste input"""
        phone = "+919876543216"
        
        # Start, age, gender
        self.handler.process_sms(phone, "PROFILE BANAO")
        self.handler.process_sms(phone, "35")
        self.handler.process_sms(phone, "1")
        
        # Enter caste (2 = OBC)
        response = self.handler.process_sms(phone, "2")
        
        assert "income" in response.lower() or "आय" in response or "उत्पन्न" in response
    
    def test_profile_creation_workflow_income(self):
        """Test profile creation - income input"""
        phone = "+919876543217"
        
        # Start, age, gender, caste
        self.handler.process_sms(phone, "PROFILE BANAO")
        self.handler.process_sms(phone, "35")
        self.handler.process_sms(phone, "1")
        self.handler.process_sms(phone, "2")
        
        # Enter income
        response = self.handler.process_sms(phone, "120000")
        
        assert "land" in response.lower() or "भूमि" in response or "जमीन" in response
    
    def test_profile_creation_workflow_land(self):
        """Test profile creation - land ownership input"""
        phone = "+919876543218"
        
        # Start, age, gender, caste, income
        self.handler.process_sms(phone, "PROFILE BANAO")
        self.handler.process_sms(phone, "35")
        self.handler.process_sms(phone, "1")
        self.handler.process_sms(phone, "2")
        self.handler.process_sms(phone, "120000")
        
        # Enter land
        response = self.handler.process_sms(phone, "2.5")
        
        assert "employment" in response.lower() or "रोजगार" in response
    
    def test_profile_creation_workflow_employment(self):
        """Test profile creation - employment input"""
        phone = "+919876543219"
        
        # Complete previous steps
        self.handler.process_sms(phone, "PROFILE BANAO")
        self.handler.process_sms(phone, "35")
        self.handler.process_sms(phone, "1")
        self.handler.process_sms(phone, "2")
        self.handler.process_sms(phone, "120000")
        self.handler.process_sms(phone, "2.5")
        
        # Enter employment (1 = farmer)
        response = self.handler.process_sms(phone, "1")
        
        assert "location" in response.lower() or "स्थान" in response
    
    def test_profile_creation_workflow_location(self):
        """Test profile creation - location input"""
        phone = "+919876543220"
        
        # Complete previous steps
        self.handler.process_sms(phone, "PROFILE BANAO")
        self.handler.process_sms(phone, "35")
        self.handler.process_sms(phone, "1")
        self.handler.process_sms(phone, "2")
        self.handler.process_sms(phone, "120000")
        self.handler.process_sms(phone, "2.5")
        self.handler.process_sms(phone, "1")
        
        # Enter location
        response = self.handler.process_sms(phone, "Maharashtra,Pune,Pirangut")
        
        assert "family" in response.lower() or "परिवार" in response or "कुटुंब" in response
    
    def test_profile_creation_complete(self):
        """Test complete profile creation workflow"""
        phone = "+919876543221"
        
        # Complete all steps
        self.handler.process_sms(phone, "PROFILE BANAO")
        self.handler.process_sms(phone, "35")
        self.handler.process_sms(phone, "1")
        self.handler.process_sms(phone, "2")
        self.handler.process_sms(phone, "120000")
        self.handler.process_sms(phone, "2.5")
        self.handler.process_sms(phone, "1")
        self.handler.process_sms(phone, "Maharashtra,Pune,Pirangut")
        
        # Enter family size
        response = self.handler.process_sms(phone, "4")
        
        assert "Profile created" in response or "प्रोफाइल बनाई गई" in response or "प्रोफाईल तयार झाली" in response
        assert "ID:" in response or "आयडी:" in response or "आईडी:" in response
    
    def test_invalid_age_input(self):
        """Test invalid age input"""
        phone = "+919876543222"
        
        self.handler.process_sms(phone, "PROFILE BANAO")
        
        # Enter invalid age
        response = self.handler.process_sms(phone, "200")
        
        assert "invalid" in response.lower() or "अमान्य" in response or "अवैध" in response
    
    def test_invalid_number_input(self):
        """Test invalid number input"""
        phone = "+919876543223"
        
        self.handler.process_sms(phone, "PROFILE BANAO")
        
        # Enter non-numeric age
        response = self.handler.process_sms(phone, "ABC")
        
        assert "invalid" in response.lower() or "अमान्य" in response or "अवैध" in response
    
    def test_help_command(self):
        """Test help command"""
        phone = "+919876543224"
        
        response = self.handler.process_sms(phone, "HELP")
        
        assert "Help" in response or "मदद" in response or "मदत" in response
    
    def test_phone_number_normalization(self):
        """Test phone number normalization"""
        # Test with country code
        normalized1 = self.handler._normalize_phone_number("+919876543210")
        assert normalized1 == "9876543210"
        
        # Test with spaces
        normalized2 = self.handler._normalize_phone_number("98765 43210")
        assert normalized2 == "9876543210"
        
        # Test with dashes
        normalized3 = self.handler._normalize_phone_number("9876-543-210")
        assert normalized3 == "9876543210"
    
    def test_session_persistence(self):
        """Test that session data persists across messages"""
        phone = "+919876543225"
        
        # First message
        self.handler.process_sms(phone, "HELLO")
        session1 = self.handler._get_session(phone)
        
        # Second message
        self.handler.process_sms(phone, "1")
        session2 = self.handler._get_session(phone)
        
        assert session1["created_at"] == session2["created_at"]
        assert session2.get("language") == SMSLanguage.HINDI
    
    def test_multiple_users_separate_sessions(self):
        """Test that multiple users have separate sessions"""
        phone1 = "+919876543226"
        phone2 = "+919876543227"
        
        # User 1 selects Hindi
        self.handler.process_sms(phone1, "HELLO")
        self.handler.process_sms(phone1, "1")
        
        # User 2 selects English
        self.handler.process_sms(phone2, "HELLO")
        self.handler.process_sms(phone2, "3")
        
        session1 = self.handler._get_session(phone1)
        session2 = self.handler._get_session(phone2)
        
        assert session1["language"] == SMSLanguage.HINDI
        assert session2["language"] == SMSLanguage.ENGLISH
    
    def test_scheme_discovery_without_profile(self):
        """Test scheme discovery without profile"""
        phone = "+919876543228"
        
        # Try to discover schemes without profile
        self.handler.process_sms(phone, "HELLO")
        self.handler.process_sms(phone, "3")  # English
        response = self.handler.process_sms(phone, "2")  # Find schemes
        
        assert "No profile" in response or "profile" in response.lower()
    
    def test_empty_message_handling(self):
        """Test handling of empty messages"""
        response = self.handler.process_sms("+919876543229", "")
        
        assert "error" in response.lower() or "Error" in response
    
    def test_invalid_phone_number_handling(self):
        """Test handling of invalid phone numbers"""
        response = self.handler.process_sms("", "HELLO")
        
        assert "error" in response.lower() or "Error" in response
