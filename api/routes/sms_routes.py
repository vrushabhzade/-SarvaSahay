"""
SMS Interface API Routes
Handles incoming SMS messages and webhook integrations
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime

router = APIRouter()


class SMSRoutes:
    """API routes for SMS interface"""
    
    def __init__(self, sms_handler):
        self.sms_handler = sms_handler
    
    def handle_incoming_sms(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming SMS webhook
        
        Expected request format:
        {
            "from": "+919876543210",
            "body": "PROFILE BANAO",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        Returns:
        {
            "to": "+919876543210",
            "message": "Response message",
            "status": "success"
        }
        """
        try:
            phone_number = request_data.get("from")
            message = request_data.get("body", "")
            
            if not phone_number or not message:
                return {
                    "status": "error",
                    "error": "Missing required fields: from, body"
                }
            
            # Process SMS through handler
            response_message = self.sms_handler.process_sms(phone_number, message)
            
            return {
                "to": phone_number,
                "message": response_message,
                "status": "success",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def send_sms(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send outbound SMS
        
        Expected request format:
        {
            "to": "+919876543210",
            "message": "Your application has been approved!"
        }
        """
        try:
            phone_number = request_data.get("to")
            message = request_data.get("message")
            
            if not phone_number or not message:
                return {
                    "status": "error",
                    "error": "Missing required fields: to, message"
                }
            
            # In production, integrate with SMS gateway (Twilio, etc.)
            # For now, just log the message
            return {
                "status": "success",
                "message_id": f"SMS-{hash(phone_number + message)}",
                "to": phone_number,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_session_status(self, phone_number: str) -> Dict[str, Any]:
        """Get current session status for a phone number"""
        try:
            session = self.sms_handler._get_session(phone_number)
            
            return {
                "status": "success",
                "phone_number": phone_number,
                "session": {
                    "state": session.get("state"),
                    "language": session.get("language"),
                    "profile_id": session.get("profile_id"),
                    "created_at": session.get("created_at"),
                    "updated_at": session.get("updated_at")
                }
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
