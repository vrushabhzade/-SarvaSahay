"""
GDPR Compliance Service
Implements data protection and privacy compliance features
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import json


class DataRequestType(str, Enum):
    """Types of GDPR data requests"""
    ACCESS = "access"  # Right to access personal data
    RECTIFICATION = "rectification"  # Right to correct inaccurate data
    ERASURE = "erasure"  # Right to be forgotten
    PORTABILITY = "portability"  # Right to data portability
    RESTRICTION = "restriction"  # Right to restrict processing
    OBJECTION = "objection"  # Right to object to processing


class RequestStatus(str, Enum):
    """Status of GDPR requests"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"


class ConsentType(str, Enum):
    """Types of user consent"""
    DATA_PROCESSING = "data_processing"
    MARKETING = "marketing"
    THIRD_PARTY_SHARING = "third_party_sharing"
    ANALYTICS = "analytics"
    PROFILING = "profiling"


@dataclass
class GDPRRequest:
    """GDPR data request"""
    request_id: str
    user_id: str
    request_type: DataRequestType
    status: RequestStatus
    created_at: str
    completed_at: Optional[str]
    requested_by: str
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class UserConsent:
    """User consent record"""
    consent_id: str
    user_id: str
    consent_type: ConsentType
    granted: bool
    granted_at: str
    withdrawn_at: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class GDPRComplianceService:
    """
    GDPR compliance service for data protection and privacy
    Implements rights under GDPR including data access, deletion, and portability
    """
    
    def __init__(self):
        # In-memory storage for demo (use database in production)
        self.gdpr_requests: Dict[str, GDPRRequest] = {}
        self.user_consents: Dict[str, List[UserConsent]] = {}
        self.deletion_queue: List[str] = []
        
        # GDPR compliance settings
        self.data_retention_days = 365 * 7  # 7 years for financial records
        self.deletion_grace_period_days = 30  # 30 days to complete deletion
        self.request_response_days = 30  # 30 days to respond to requests
    
    def create_data_request(
        self,
        user_id: str,
        request_type: DataRequestType,
        requested_by: str,
        details: Optional[Dict[str, Any]] = None
    ) -> GDPRRequest:
        """
        Create a GDPR data request
        
        Args:
            user_id: User ID for the request
            request_type: Type of GDPR request
            requested_by: Who is making the request
            details: Additional request details
            
        Returns:
            Created GDPR request
        """
        import hashlib
        
        # Generate request ID
        request_id = hashlib.sha256(
            f"{user_id}-{request_type.value}-{datetime.utcnow().timestamp()}".encode()
        ).hexdigest()[:16]
        
        # Create request
        request = GDPRRequest(
            request_id=request_id,
            user_id=user_id,
            request_type=request_type,
            status=RequestStatus.PENDING,
            created_at=datetime.utcnow().isoformat(),
            completed_at=None,
            requested_by=requested_by,
            details=details or {}
        )
        
        self.gdpr_requests[request_id] = request
        
        # Add to deletion queue if erasure request
        if request_type == DataRequestType.ERASURE:
            self.deletion_queue.append(user_id)
        
        return request
    
    def process_access_request(
        self,
        request_id: str,
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a data access request
        Returns all personal data held about the user
        
        Args:
            request_id: GDPR request ID
            user_data: User's personal data from all systems
            
        Returns:
            Packaged user data for export
        """
        if request_id not in self.gdpr_requests:
            raise ValueError(f"Request {request_id} not found")
        
        request = self.gdpr_requests[request_id]
        
        if request.request_type != DataRequestType.ACCESS:
            raise ValueError(f"Request {request_id} is not an access request")
        
        # Update request status
        request.status = RequestStatus.IN_PROGRESS
        
        # Package user data
        packaged_data = {
            'request_id': request_id,
            'user_id': request.user_id,
            'generated_at': datetime.utcnow().isoformat(),
            'data': user_data,
            'metadata': {
                'data_sources': list(user_data.keys()),
                'total_records': sum(
                    len(v) if isinstance(v, list) else 1
                    for v in user_data.values()
                )
            }
        }
        
        # Mark request as completed
        request.status = RequestStatus.COMPLETED
        request.completed_at = datetime.utcnow().isoformat()
        
        return packaged_data
    
    def process_erasure_request(
        self,
        request_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Process a data erasure request (right to be forgotten)
        
        Args:
            request_id: GDPR request ID
            user_id: User ID to delete
            
        Returns:
            Deletion confirmation with details
        """
        if request_id not in self.gdpr_requests:
            raise ValueError(f"Request {request_id} not found")
        
        request = self.gdpr_requests[request_id]
        
        if request.request_type != DataRequestType.ERASURE:
            raise ValueError(f"Request {request_id} is not an erasure request")
        
        # Update request status
        request.status = RequestStatus.IN_PROGRESS
        
        # Calculate deletion date (grace period)
        deletion_date = datetime.utcnow() + timedelta(
            days=self.deletion_grace_period_days
        )
        
        # In production, this would trigger actual data deletion across all systems
        deletion_result = {
            'request_id': request_id,
            'user_id': user_id,
            'status': 'scheduled',
            'scheduled_deletion_date': deletion_date.isoformat(),
            'grace_period_days': self.deletion_grace_period_days,
            'data_to_delete': [
                'user_profile',
                'documents',
                'applications',
                'audit_logs',
                'consents'
            ],
            'retention_exceptions': [
                'Legal requirement: Financial transaction records (7 years)',
                'Legal requirement: Tax records (7 years)'
            ]
        }
        
        # Mark request as completed
        request.status = RequestStatus.COMPLETED
        request.completed_at = datetime.utcnow().isoformat()
        
        return deletion_result
    
    def process_portability_request(
        self,
        request_id: str,
        user_data: Dict[str, Any],
        format: str = 'json'
    ) -> str:
        """
        Process a data portability request
        Returns user data in machine-readable format
        
        Args:
            request_id: GDPR request ID
            user_data: User's personal data
            format: Export format ('json' or 'csv')
            
        Returns:
            Exported data as string
        """
        if request_id not in self.gdpr_requests:
            raise ValueError(f"Request {request_id} not found")
        
        request = self.gdpr_requests[request_id]
        
        if request.request_type != DataRequestType.PORTABILITY:
            raise ValueError(f"Request {request_id} is not a portability request")
        
        # Update request status
        request.status = RequestStatus.IN_PROGRESS
        
        # Export data in requested format
        if format == 'json':
            exported_data = json.dumps(user_data, indent=2)
        elif format == 'csv':
            # Simplified CSV export
            lines = []
            for key, value in user_data.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        lines.append(f"{key}.{sub_key},{sub_value}")
                else:
                    lines.append(f"{key},{value}")
            exported_data = '\n'.join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Mark request as completed
        request.status = RequestStatus.COMPLETED
        request.completed_at = datetime.utcnow().isoformat()
        
        return exported_data
    
    def record_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        granted: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserConsent:
        """
        Record user consent
        
        Args:
            user_id: User ID
            consent_type: Type of consent
            granted: Whether consent is granted or withdrawn
            ip_address: IP address of the request
            user_agent: User agent string
            
        Returns:
            Created consent record
        """
        import hashlib
        
        # Generate consent ID
        consent_id = hashlib.sha256(
            f"{user_id}-{consent_type.value}-{datetime.utcnow().timestamp()}".encode()
        ).hexdigest()[:16]
        
        # Create consent record
        consent = UserConsent(
            consent_id=consent_id,
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            granted_at=datetime.utcnow().isoformat(),
            withdrawn_at=None if granted else datetime.utcnow().isoformat(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Store consent
        if user_id not in self.user_consents:
            self.user_consents[user_id] = []
        
        self.user_consents[user_id].append(consent)
        
        return consent
    
    def get_user_consents(self, user_id: str) -> List[UserConsent]:
        """Get all consent records for a user"""
        return self.user_consents.get(user_id, [])
    
    def check_consent(
        self,
        user_id: str,
        consent_type: ConsentType
    ) -> bool:
        """
        Check if user has given consent for a specific purpose
        
        Args:
            user_id: User ID
            consent_type: Type of consent to check
            
        Returns:
            True if consent is granted, False otherwise
        """
        user_consents = self.user_consents.get(user_id, [])
        
        # Get most recent consent of this type
        relevant_consents = [
            c for c in user_consents
            if c.consent_type == consent_type
        ]
        
        if not relevant_consents:
            return False
        
        # Sort by granted_at and get most recent
        latest_consent = sorted(
            relevant_consents,
            key=lambda c: c.granted_at,
            reverse=True
        )[0]
        
        return latest_consent.granted and latest_consent.withdrawn_at is None
    
    def get_request_status(self, request_id: str) -> Optional[GDPRRequest]:
        """Get status of a GDPR request"""
        return self.gdpr_requests.get(request_id)
    
    def get_user_requests(self, user_id: str) -> List[GDPRRequest]:
        """Get all GDPR requests for a user"""
        return [
            request for request in self.gdpr_requests.values()
            if request.user_id == user_id
        ]
    
    def get_pending_requests(self) -> List[GDPRRequest]:
        """Get all pending GDPR requests"""
        return [
            request for request in self.gdpr_requests.values()
            if request.status == RequestStatus.PENDING
        ]
    
    def get_overdue_requests(self) -> List[GDPRRequest]:
        """Get requests that are overdue (>30 days)"""
        cutoff_date = datetime.utcnow() - timedelta(days=self.request_response_days)
        
        return [
            request for request in self.gdpr_requests.values()
            if request.status in [RequestStatus.PENDING, RequestStatus.IN_PROGRESS]
            and datetime.fromisoformat(request.created_at) < cutoff_date
        ]
    
    def anonymize_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymize user data for retention purposes
        Removes personally identifiable information while keeping statistical data
        
        Args:
            user_data: User data to anonymize
            
        Returns:
            Anonymized user data
        """
        anonymized = user_data.copy()
        
        # Fields to anonymize
        pii_fields = [
            'name', 'email', 'phone', 'phone_number', 'address',
            'aadhaar', 'pan', 'bank_account', 'voter_id'
        ]
        
        def anonymize_dict(d: Dict[str, Any]) -> Dict[str, Any]:
            """Recursively anonymize dictionary"""
            result = {}
            for key, value in d.items():
                if key in pii_fields:
                    result[key] = '[REDACTED]'
                elif isinstance(value, dict):
                    result[key] = anonymize_dict(value)
                elif isinstance(value, list):
                    result[key] = [
                        anonymize_dict(item) if isinstance(item, dict) else '[REDACTED]'
                        for item in value
                    ]
                else:
                    result[key] = value
            return result
        
        return anonymize_dict(anonymized)
    
    def generate_compliance_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate GDPR compliance report
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Compliance report with statistics
        """
        # Filter requests by date
        filtered_requests = list(self.gdpr_requests.values())
        
        if start_date:
            filtered_requests = [
                r for r in filtered_requests
                if datetime.fromisoformat(r.created_at) >= start_date
            ]
        
        if end_date:
            filtered_requests = [
                r for r in filtered_requests
                if datetime.fromisoformat(r.created_at) <= end_date
            ]
        
        # Count by request type
        request_type_counts = {}
        for request in filtered_requests:
            req_type = request.request_type.value
            request_type_counts[req_type] = request_type_counts.get(req_type, 0) + 1
        
        # Count by status
        status_counts = {}
        for request in filtered_requests:
            status = request.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Calculate average response time
        completed_requests = [
            r for r in filtered_requests
            if r.status == RequestStatus.COMPLETED and r.completed_at
        ]
        
        avg_response_time = 0
        if completed_requests:
            total_time = sum(
                (datetime.fromisoformat(r.completed_at) - 
                 datetime.fromisoformat(r.created_at)).total_seconds()
                for r in completed_requests
            )
            avg_response_time = total_time / len(completed_requests) / 86400  # Convert to days
        
        return {
            'report_period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'total_requests': len(filtered_requests),
            'request_type_counts': request_type_counts,
            'status_counts': status_counts,
            'pending_requests': status_counts.get('pending', 0),
            'overdue_requests': len(self.get_overdue_requests()),
            'average_response_time_days': round(avg_response_time, 2),
            'compliance_rate': (
                status_counts.get('completed', 0) / len(filtered_requests) * 100
                if filtered_requests else 0
            )
        }


# Global GDPR compliance service instance
_gdpr_service: Optional[GDPRComplianceService] = None


def get_gdpr_service() -> GDPRComplianceService:
    """Get or create global GDPR compliance service instance"""
    global _gdpr_service
    if _gdpr_service is None:
        _gdpr_service = GDPRComplianceService()
    return _gdpr_service
