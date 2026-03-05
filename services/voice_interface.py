"""
SarvaSahay Voice Interface Handler
Speech-to-text conversion and voice-guided interaction
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime


class VoiceLanguage(str, Enum):
    """Supported voice languages"""
    HINDI = "hi-IN"
    MARATHI = "mr-IN"
    ENGLISH = "en-IN"
    TAMIL = "ta-IN"
    BENGALI = "bn-IN"
    TELUGU = "te-IN"
    KANNADA = "kn-IN"
    GUJARATI = "gu-IN"


class VoiceCallState(str, Enum):
    """Voice call conversation states"""
    INITIAL = "initial"
    LANGUAGE_SELECTION = "language_selection"
    MAIN_MENU = "main_menu"
    PROFILE_CREATION = "profile_creation"
    SCHEME_DISCOVERY = "scheme_discovery"
    APPLICATION_STATUS = "application_status"


class VoiceInterfaceHandler:
    """
    Voice interface handler for non-literate users
    Provides speech-to-text conversion and voice-guided navigation
    """
    
    def __init__(self, sms_handler=None, profile_service=None, eligibility_service=None):
        self.sms_handler = sms_handler  # Reuse SMS logic for state management
        self.profile_service = profile_service
        self.eligibility_service = eligibility_service
        self.call_sessions = {}  # Store call sessions: call_id -> session_data
        self.voice_prompts = self._load_voice_prompts()
    
    def process_voice_input(self, call_id: str, phone_number: str, 
                           speech_text: str, language: str = "en-IN") -> Dict[str, Any]:
        """
        Process voice input and return voice response
        
        Args:
            call_id: Unique call identifier
            phone_number: Caller's phone number
            speech_text: Transcribed speech text
            language: Voice language code (e.g., "hi-IN" for Hindi)
            
        Returns:
            Dict with voice response and call control instructions
        """
        if not call_id or not phone_number:
            return self._get_error_response(language)
        
        # Get or create call session
        session = self._get_call_session(call_id, phone_number, language)
        
        # Convert speech to text (already done by caller, but validate)
        if not speech_text or speech_text.strip() == "":
            return self._get_prompt_response("no_input", language)
        
        # Process through SMS handler for state management
        if self.sms_handler:
            sms_response = self.sms_handler.process_sms(phone_number, speech_text)
            
            # Convert SMS response to voice response
            return {
                "call_id": call_id,
                "response_text": sms_response,
                "response_audio_url": None,  # In production, convert text to speech
                "language": language,
                "action": "continue",  # continue, end, transfer
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Fallback if no SMS handler
        return self._get_prompt_response("service_unavailable", language)
    
    def start_voice_call(self, call_id: str, phone_number: str, 
                        preferred_language: Optional[str] = None) -> Dict[str, Any]:
        """
        Initialize a voice call session
        
        Args:
            call_id: Unique call identifier
            phone_number: Caller's phone number
            preferred_language: Preferred language code
            
        Returns:
            Initial voice prompt
        """
        language = preferred_language or VoiceLanguage.HINDI
        
        # Create call session
        session = {
            "call_id": call_id,
            "phone_number": phone_number,
            "language": language,
            "state": VoiceCallState.INITIAL,
            "created_at": datetime.utcnow().isoformat()
        }
        self.call_sessions[call_id] = session
        
        # Return welcome message
        return {
            "call_id": call_id,
            "response_text": self._get_voice_prompt("welcome", language),
            "response_audio_url": None,
            "language": language,
            "action": "continue",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def end_voice_call(self, call_id: str) -> Dict[str, Any]:
        """End a voice call session"""
        if call_id in self.call_sessions:
            session = self.call_sessions[call_id]
            language = session.get("language", VoiceLanguage.HINDI)
            del self.call_sessions[call_id]
            
            return {
                "call_id": call_id,
                "response_text": self._get_voice_prompt("goodbye", language),
                "response_audio_url": None,
                "language": language,
                "action": "end",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {"call_id": call_id, "action": "end"}
    
    def convert_speech_to_text(self, audio_data: bytes, language: str = "hi-IN") -> str:
        """
        Convert speech audio to text using NLP processor
        
        Args:
            audio_data: Audio data in bytes
            language: Language code for speech recognition
            
        Returns:
            Transcribed text
        """
        # In production, integrate with speech recognition service
        # (Google Speech-to-Text, Azure Speech, etc.)
        # For now, return mock transcription
        return "[Mock transcription - integrate with speech recognition API]"
    
    def convert_text_to_speech(self, text: str, language: str = "hi-IN") -> bytes:
        """
        Convert text to speech audio
        
        Args:
            text: Text to convert
            language: Language code for speech synthesis
            
        Returns:
            Audio data in bytes
        """
        # In production, integrate with text-to-speech service
        # (Google Text-to-Speech, Azure Speech, etc.)
        # For now, return mock audio
        return b"[Mock audio data - integrate with TTS API]"
    
    def _get_call_session(self, call_id: str, phone_number: str, language: str) -> Dict:
        """Get or create call session"""
        if call_id not in self.call_sessions:
            self.call_sessions[call_id] = {
                "call_id": call_id,
                "phone_number": phone_number,
                "language": language,
                "state": VoiceCallState.INITIAL,
                "created_at": datetime.utcnow().isoformat()
            }
        return self.call_sessions[call_id]
    
    def _get_voice_prompt(self, key: str, language: str) -> str:
        """Get voice prompt in specified language"""
        lang_code = self._normalize_language_code(language)
        return self.voice_prompts.get(lang_code, {}).get(key, 
                                                         self.voice_prompts["en-IN"].get(key, ""))
    
    def _get_prompt_response(self, prompt_key: str, language: str) -> Dict[str, Any]:
        """Get formatted prompt response"""
        return {
            "response_text": self._get_voice_prompt(prompt_key, language),
            "response_audio_url": None,
            "language": language,
            "action": "continue",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _get_error_response(self, language: str) -> Dict[str, Any]:
        """Get error response"""
        return {
            "response_text": self._get_voice_prompt("error", language),
            "response_audio_url": None,
            "language": language,
            "action": "end",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _normalize_language_code(self, language: str) -> str:
        """Normalize language code to standard format"""
        # Map various formats to standard codes
        lang_map = {
            "hindi": "hi-IN",
            "marathi": "mr-IN",
            "english": "en-IN",
            "tamil": "ta-IN",
            "bengali": "bn-IN",
            "telugu": "te-IN",
            "kannada": "kn-IN",
            "gujarati": "gu-IN"
        }
        return lang_map.get(language.lower(), language)
    
    def _load_voice_prompts(self) -> Dict[str, Dict[str, str]]:
        """Load voice prompt templates"""
        return {
            "hi-IN": {
                "welcome": "सर्वसहाय में आपका स्वागत है। सरकारी योजनाओं के बारे में जानने के लिए, कृपया अपनी जानकारी साझा करें।",
                "goodbye": "सर्वसहाय का उपयोग करने के लिए धन्यवाद। नमस्ते।",
                "no_input": "क्षमा करें, मैंने आपको नहीं सुना। कृपया फिर से बोलें।",
                "service_unavailable": "क्षमा करें, सेवा अभी उपलब्ध नहीं है। कृपया बाद में पुनः प्रयास करें।",
                "error": "कुछ गलत हो गया। कृपया बाद में पुनः प्रयास करें।"
            },
            "mr-IN": {
                "welcome": "सर्वसहाय मध्ये आपले स्वागत आहे। सरकारी योजनांबद्दल जाणून घेण्यासाठी, कृपया आपली माहिती शेअर करा।",
                "goodbye": "सर्वसहाय वापरल्याबद्दल धन्यवाद। नमस्कार।",
                "no_input": "माफ करा, मी तुम्हाला ऐकले नाही. कृपया पुन्हा बोला.",
                "service_unavailable": "माफ करा, सेवा सध्या उपलब्ध नाही. कृपया नंतर पुन्हा प्रयत्न करा.",
                "error": "काहीतरी चूक झाली. कृपया नंतर पुन्हा प्रयत्न करा."
            },
            "en-IN": {
                "welcome": "Welcome to SarvaSahay. To learn about government schemes, please share your information.",
                "goodbye": "Thank you for using SarvaSahay. Goodbye.",
                "no_input": "Sorry, I didn't hear you. Please speak again.",
                "service_unavailable": "Sorry, the service is currently unavailable. Please try again later.",
                "error": "Something went wrong. Please try again later."
            }
        }
