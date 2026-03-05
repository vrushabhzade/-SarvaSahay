"""
Unit tests for Voice Interface Handler
Tests speech-to-text conversion and voice-guided interaction
"""

import pytest
from services.voice_interface import VoiceInterfaceHandler, VoiceLanguage, VoiceCallState
from services.sms_interface import SMSInterfaceHandler


class TestVoiceInterfaceHandler:
    """Test voice interface handler functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.sms_handler = SMSInterfaceHandler()
        self.handler = VoiceInterfaceHandler(sms_handler=self.sms_handler)
    
    def test_start_voice_call(self):
        """Test starting a voice call"""
        call_id = "CALL-001"
        phone = "+919876543210"
        
        response = self.handler.start_voice_call(call_id, phone)
        
        assert response["call_id"] == call_id
        assert "Welcome" in response["response_text"] or "स्वागत" in response["response_text"]
        assert response["action"] == "continue"
    
    def test_start_voice_call_with_language(self):
        """Test starting a voice call with specific language"""
        call_id = "CALL-002"
        phone = "+919876543211"
        
        response = self.handler.start_voice_call(call_id, phone, VoiceLanguage.MARATHI)
        
        assert response["call_id"] == call_id
        assert response["language"] == VoiceLanguage.MARATHI
        assert "स्वागत" in response["response_text"]
    
    def test_end_voice_call(self):
        """Test ending a voice call"""
        call_id = "CALL-003"
        phone = "+919876543212"
        
        # Start call first
        self.handler.start_voice_call(call_id, phone)
        
        # End call
        response = self.handler.end_voice_call(call_id)
        
        assert response["call_id"] == call_id
        assert response["action"] == "end"
        assert "Thank you" in response["response_text"] or "धन्यवाद" in response["response_text"]
    
    def test_process_voice_input_with_sms_handler(self):
        """Test processing voice input through SMS handler"""
        call_id = "CALL-004"
        phone = "+919876543213"
        
        # Start call
        self.handler.start_voice_call(call_id, phone, VoiceLanguage.ENGLISH)
        
        # Process voice input (profile creation command)
        response = self.handler.process_voice_input(
            call_id, phone, "CREATE PROFILE", "en-IN"
        )
        
        assert response["call_id"] == call_id
        assert "age" in response["response_text"].lower()
        assert response["action"] == "continue"
    
    def test_process_voice_input_profile_workflow(self):
        """Test complete profile creation via voice"""
        call_id = "CALL-005"
        phone = "+919876543214"
        
        # Start call
        self.handler.start_voice_call(call_id, phone, VoiceLanguage.ENGLISH)
        
        # Profile creation workflow
        self.handler.process_voice_input(call_id, phone, "PROFILE BANAO", "hi-IN")
        
        # Age
        response = self.handler.process_voice_input(call_id, phone, "35", "hi-IN")
        assert "gender" in response["response_text"].lower() or "लिंग" in response["response_text"]
        
        # Gender
        response = self.handler.process_voice_input(call_id, phone, "1", "hi-IN")
        assert "category" in response["response_text"].lower() or "श्रेणी" in response["response_text"]
    
    def test_process_empty_voice_input(self):
        """Test handling empty voice input"""
        call_id = "CALL-006"
        phone = "+919876543215"
        
        self.handler.start_voice_call(call_id, phone)
        
        response = self.handler.process_voice_input(call_id, phone, "", "hi-IN")
        
        assert "no_input" in response["response_text"].lower() or "नहीं सुना" in response["response_text"]
    
    def test_language_normalization(self):
        """Test language code normalization"""
        assert self.handler._normalize_language_code("hindi") == "hi-IN"
        assert self.handler._normalize_language_code("marathi") == "mr-IN"
        assert self.handler._normalize_language_code("english") == "en-IN"
        assert self.handler._normalize_language_code("hi-IN") == "hi-IN"
    
    def test_voice_prompts_hindi(self):
        """Test Hindi voice prompts"""
        prompt = self.handler._get_voice_prompt("welcome", "hi-IN")
        assert "सर्वसहाय" in prompt
        assert "स्वागत" in prompt
    
    def test_voice_prompts_marathi(self):
        """Test Marathi voice prompts"""
        prompt = self.handler._get_voice_prompt("welcome", "mr-IN")
        assert "सर्वसहाय" in prompt
        assert "स्वागत" in prompt
    
    def test_voice_prompts_english(self):
        """Test English voice prompts"""
        prompt = self.handler._get_voice_prompt("welcome", "en-IN")
        assert "Welcome" in prompt
        assert "SarvaSahay" in prompt
    
    def test_call_session_creation(self):
        """Test call session is created and stored"""
        call_id = "CALL-007"
        phone = "+919876543216"
        
        self.handler.start_voice_call(call_id, phone)
        
        assert call_id in self.handler.call_sessions
        session = self.handler.call_sessions[call_id]
        assert session["phone_number"] == phone
        assert session["state"] == VoiceCallState.INITIAL
    
    def test_call_session_cleanup(self):
        """Test call session is cleaned up after end"""
        call_id = "CALL-008"
        phone = "+919876543217"
        
        self.handler.start_voice_call(call_id, phone)
        assert call_id in self.handler.call_sessions
        
        self.handler.end_voice_call(call_id)
        assert call_id not in self.handler.call_sessions
    
    def test_multiple_concurrent_calls(self):
        """Test handling multiple concurrent calls"""
        call1 = "CALL-009"
        call2 = "CALL-010"
        phone1 = "+919876543218"
        phone2 = "+919876543219"
        
        # Start both calls
        self.handler.start_voice_call(call1, phone1, VoiceLanguage.HINDI)
        self.handler.start_voice_call(call2, phone2, VoiceLanguage.ENGLISH)
        
        # Verify both sessions exist
        assert call1 in self.handler.call_sessions
        assert call2 in self.handler.call_sessions
        
        # Verify languages are different
        assert self.handler.call_sessions[call1]["language"] == VoiceLanguage.HINDI
        assert self.handler.call_sessions[call2]["language"] == VoiceLanguage.ENGLISH
    
    def test_convert_speech_to_text_mock(self):
        """Test speech-to-text conversion (mock)"""
        audio_data = b"mock audio data"
        result = self.handler.convert_speech_to_text(audio_data, "hi-IN")
        
        # Mock implementation returns placeholder
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_convert_text_to_speech_mock(self):
        """Test text-to-speech conversion (mock)"""
        text = "Hello, welcome to SarvaSahay"
        result = self.handler.convert_text_to_speech(text, "en-IN")
        
        # Mock implementation returns placeholder
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_error_response_format(self):
        """Test error response format"""
        response = self.handler._get_error_response("en-IN")
        
        assert "response_text" in response
        assert "language" in response
        assert "action" in response
        assert response["action"] == "end"
    
    def test_prompt_response_format(self):
        """Test prompt response format"""
        response = self.handler._get_prompt_response("welcome", "hi-IN")
        
        assert "response_text" in response
        assert "language" in response
        assert "action" in response
        assert response["action"] == "continue"
