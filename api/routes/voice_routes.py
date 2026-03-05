"""
Voice Interface API Routes
Handles voice call webhooks and speech processing
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime

router = APIRouter()


class VoiceRoutes:
    """API routes for voice interface"""
    
    def __init__(self, voice_handler):
        self.voice_handler = voice_handler
    
    def handle_incoming_call(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming voice call
        
        Expected request format:
        {
            "call_id": "CALL-12345",
            "from": "+919876543210",
            "language": "hi-IN"
        }
        """
        try:
            call_id = request_data.get("call_id")
            phone_number = request_data.get("from")
            language = request_data.get("language", "hi-IN")
            
            if not call_id or not phone_number:
                return {
                    "status": "error",
                    "error": "Missing required fields: call_id, from"
                }
            
            # Start voice call session
            response = self.voice_handler.start_voice_call(call_id, phone_number, language)
            
            return {
                "status": "success",
                **response
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def handle_voice_input(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle voice input during call
        
        Expected request format:
        {
            "call_id": "CALL-12345",
            "from": "+919876543210",
            "speech_text": "मेरी उम्र 35 साल है",
            "language": "hi-IN"
        }
        """
        try:
            call_id = request_data.get("call_id")
            phone_number = request_data.get("from")
            speech_text = request_data.get("speech_text", "")
            language = request_data.get("language", "hi-IN")
            
            if not call_id or not phone_number:
                return {
                    "status": "error",
                    "error": "Missing required fields: call_id, from"
                }
            
            # Process voice input
            response = self.voice_handler.process_voice_input(
                call_id, phone_number, speech_text, language
            )
            
            return {
                "status": "success",
                **response
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def handle_call_end(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle call termination
        
        Expected request format:
        {
            "call_id": "CALL-12345"
        }
        """
        try:
            call_id = request_data.get("call_id")
            
            if not call_id:
                return {
                    "status": "error",
                    "error": "Missing required field: call_id"
                }
            
            # End voice call session
            response = self.voice_handler.end_voice_call(call_id)
            
            return {
                "status": "success",
                **response
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def handle_speech_to_text(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert speech audio to text
        
        Expected request format:
        {
            "audio_url": "https://example.com/audio.wav",
            "language": "hi-IN"
        }
        """
        try:
            audio_url = request_data.get("audio_url")
            language = request_data.get("language", "hi-IN")
            
            if not audio_url:
                return {
                    "status": "error",
                    "error": "Missing required field: audio_url"
                }
            
            # In production, fetch audio from URL and convert
            # For now, return mock transcription
            transcribed_text = "[Mock transcription]"
            
            return {
                "status": "success",
                "transcribed_text": transcribed_text,
                "language": language,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
