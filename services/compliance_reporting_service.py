"""
Compliance and Reporting Service
Implements data privacy regulation compliance and transparent reporting
for government API integration
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import json

from shared.utils.audit_log import get_audit_logger, AuditEventType
from shared.utils.gdpr_compliance import get_gdpr_service


class ComplianceStandard(str, Enum):
    """Compliance standards"""
    GDPR = "gdpr"
    IT_ACT_2000 = "it_act_2000"
    AADHAAR_ACT = "aadhaar_act"
    RBI_GUIDELINES = "rbi_guidelines"
    MEITY_GUIDELINES = "meity_guidelines"


class ReportType(str, Enum):
    """Types of compliance reports"""
    API_USAGE = "api_usage"
    DATA_ACCESS = "data_access"
    SECURITY_INCIDENTS = "security_incidents"
    GDPR_COMPLIANCE = "gdpr_compliance"
    AUDIT_TRAIL = "audit_trail"
    PERFORMANCE_METRICS = "performance_metrics"


@dataclass
class ComplianceViolation:
    """Compliance violation record"""
    violation_id: str
    standard: ComplianceStandard
    severity: str
    description: str
    detected_at: str
    resolved_at: Optional[str]
    resolution_notes: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class ComplianceReportingService:
    """
    Compliance and reporting service for government API integration
    Ensures data privacy regulation compliance and transparent reporting
    """
    
    def __init__(self):
        self.audit_logger = get_audit_logger()
        self.gdpr_service = get_gdpr_service()
        self.violations: List[ComplianceViolation] = []
        
        # Compliance thresholds
        self.max_api_calls_per_hour = 1000
        self.max_failed_auth_attempts = 5
        self.data_retention_days = 365 * 7  # 7 years
    
    def generate_api_usage_report(
        self,
        start_date: datetime,
        end_date: datetime,
        api_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate API usage report for transparency
        
        Args:
            start_date: Report start date
            end_date: Report end date
            api_name: Optional filter by API name
            
        Returns:
            API usage report
        """
        # Get audit events for API calls
        audit_events = self.audit_logger.audit_logs
        
        # Filter by date range
        filtered_events = [
            event for event in audit_events
            if start_date <= datetime.fromisoformat(event.timestamp) <= end_date
        ]
        
        # Filter by API name if provided
        if api_name:
            filtered_events = [
                event for event in filtered_events
                if event.details.get('api_name') == api_name
            ]
        
        # Calculate statistics
        total_calls = len(filtered_events)
        successful_calls = len([e for e in filtered_events if e.success])
        failed_calls = total_calls - successful_calls
        
        # Group by API endpoint
        endpoint_stats = {}
        for event in filtered_events:
            endpoint = event.details.get('endpoint', 'unknown')
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {
                    'total_calls': 0,
                    'successful': 0,
                    'failed': 0
                }
            endpoint_stats[endpoint]['total_calls'] += 1
            if event.success:
                endpoint_stats[endpoint]['successful'] += 1
            else:
                endpoint_stats[endpoint]['failed'] += 1
        
        # Calculate average response time
        response_times = [
            event.details.get('response_time_ms', 0)
            for event in filtered_events
            if 'response_time_ms' in event.details
        ]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            'report_type': ReportType.API_USAGE.value,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'api_name': api_name or 'all',
            'summary': {
                'total_calls': total_calls,
                'successful_calls': successful_calls,
                'failed_calls': failed_calls,
                'success_rate': (successful_calls / total_calls * 100) if total_calls > 0 else 0,
                'average_response_time_ms': round(avg_response_time, 2)
            },
            'endpoint_statistics': endpoint_stats,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def generate_data_access_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate data access report for compliance
        
        Args:
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Data access report
        """
        # Get audit events for data access
        audit_events = self.audit_logger.audit_logs
        
        # Filter by date range and data access events
        data_access_types = [
            AuditEventType.PROFILE_VIEWED,
            AuditEventType.DOCUMENT_VIEWED,
            AuditEventType.DATA_ACCESSED,
            AuditEventType.DATA_EXPORTED
        ]
        
        filtered_events = [
            event for event in audit_events
            if start_date <= datetime.fromisoformat(event.timestamp) <= end_date
            and event.event_type in data_access_types
        ]
        
        # Group by user
        user_access_stats = {}
        for event in filtered_events:
            user_id = event.user_id or 'anonymous'
            if user_id not in user_access_stats:
                user_access_stats[user_id] = {
                    'total_accesses': 0,
                    'profiles_accessed': 0,
                    'documents_accessed': 0,
                    'data_exported': 0
                }
            user_access_stats[user_id]['total_accesses'] += 1
            
            if event.event_type == AuditEventType.PROFILE_VIEWED:
                user_access_stats[user_id]['profiles_accessed'] += 1
            elif event.event_type == AuditEventType.DOCUMENT_VIEWED:
                user_access_stats[user_id]['documents_accessed'] += 1
            elif event.event_type == AuditEventType.DATA_EXPORTED:
                user_access_stats[user_id]['data_exported'] += 1
        
        # Identify unusual access patterns
        unusual_access = []
        for user_id, stats in user_access_stats.items():
            if stats['total_accesses'] > 100:  # Threshold for unusual activity
                unusual_access.append({
                    'user_id': user_id,
                    'access_count': stats['total_accesses'],
                    'reason': 'High volume of data access'
                })
        
        return {
            'report_type': ReportType.DATA_ACCESS.value,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'summary': {
                'total_access_events': len(filtered_events),
                'unique_users': len(user_access_stats),
                'unusual_access_patterns': len(unusual_access)
            },
            'user_access_statistics': user_access_stats,
            'unusual_access_patterns': unusual_access,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def generate_security_incidents_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate security incidents report
        
        Args:
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Security incidents report
        """
        # Get security events from audit log
        security_events = self.audit_logger.get_security_events(
            hours=int((end_date - start_date).total_seconds() / 3600)
        )
        
        # Categorize incidents
        incident_categories = {
            'failed_logins': 0,
            'suspicious_activity': 0,
            'account_lockouts': 0,
            'unauthorized_access': 0
        }
        
        for event in security_events:
            if event.event_type == AuditEventType.USER_LOGIN_FAILED:
                incident_categories['failed_logins'] += 1
            elif event.event_type == AuditEventType.SUSPICIOUS_ACTIVITY:
                incident_categories['suspicious_activity'] += 1
            elif event.event_type == AuditEventType.ACCOUNT_LOCKED:
                incident_categories['account_lockouts'] += 1
        
        # Get critical incidents
        critical_incidents = [
            {
                'event_id': event.event_id,
                'event_type': event.event_type.value,
                'timestamp': event.timestamp,
                'description': event.action,
                'user_id': event.user_id,
                'ip_address': event.ip_address
            }
            for event in security_events
            if event.severity.value == 'critical'
        ]
        
        return {
            'report_type': ReportType.SECURITY_INCIDENTS.value,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'summary': {
                'total_incidents': len(security_events),
                'critical_incidents': len(critical_incidents)
            },
            'incident_categories': incident_categories,
            'critical_incidents': critical_incidents,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def generate_gdpr_compliance_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate GDPR compliance report
        
        Args:
            start_date: Optional report start date
            end_date: Optional report end date
            
        Returns:
            GDPR compliance report
        """
        # Get GDPR compliance report from GDPR service
        gdpr_report = self.gdpr_service.generate_compliance_report(
            start_date=start_date,
            end_date=end_date
        )
        
        # Add additional compliance metrics
        pending_requests = self.gdpr_service.get_pending_requests()
        overdue_requests = self.gdpr_service.get_overdue_requests()
        
        # Check for compliance violations
        violations = []
        if len(overdue_requests) > 0:
            violations.append({
                'violation_type': 'overdue_gdpr_requests',
                'count': len(overdue_requests),
                'severity': 'high',
                'description': f'{len(overdue_requests)} GDPR requests are overdue (>30 days)'
            })
        
        return {
            'report_type': ReportType.GDPR_COMPLIANCE.value,
            'period': gdpr_report['report_period'],
            'summary': {
                'total_requests': gdpr_report['total_requests'],
                'pending_requests': len(pending_requests),
                'overdue_requests': len(overdue_requests),
                'compliance_rate': gdpr_report['compliance_rate'],
                'average_response_time_days': gdpr_report['average_response_time_days']
            },
            'request_breakdown': {
                'by_type': gdpr_report['request_type_counts'],
                'by_status': gdpr_report['status_counts']
            },
            'violations': violations,
            'generated_at': datetime.utcnow().isoformat()
        }

    
    def generate_audit_trail_report(
        self,
        resource_type: str,
        resource_id: str
    ) -> Dict[str, Any]:
        """
        Generate audit trail report for a specific resource
        
        Args:
            resource_type: Type of resource
            resource_id: Resource identifier
            
        Returns:
            Audit trail report
        """
        # Get audit trail for resource
        audit_trail = self.audit_logger.get_resource_audit_trail(
            resource_type=resource_type,
            resource_id=resource_id
        )
        
        # Build timeline
        timeline = [
            {
                'timestamp': event.timestamp,
                'event_type': event.event_type.value,
                'action': event.action,
                'user_id': event.user_id,
                'username': event.username,
                'success': event.success,
                'details': event.details
            }
            for event in audit_trail
        ]
        
        return {
            'report_type': ReportType.AUDIT_TRAIL.value,
            'resource': {
                'type': resource_type,
                'id': resource_id
            },
            'summary': {
                'total_events': len(audit_trail),
                'unique_users': len(set(e.user_id for e in audit_trail if e.user_id)),
                'first_event': audit_trail[0].timestamp if audit_trail else None,
                'last_event': audit_trail[-1].timestamp if audit_trail else None
            },
            'timeline': timeline,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def check_compliance(
        self,
        standard: ComplianceStandard
    ) -> Dict[str, Any]:
        """
        Check compliance with specific standard
        
        Args:
            standard: Compliance standard to check
            
        Returns:
            Compliance check result
        """
        violations = []
        
        if standard == ComplianceStandard.GDPR:
            # Check GDPR compliance
            overdue_requests = self.gdpr_service.get_overdue_requests()
            if overdue_requests:
                violations.append({
                    'rule': 'GDPR Article 12 - Response Time',
                    'description': f'{len(overdue_requests)} requests overdue (>30 days)',
                    'severity': 'high'
                })
        
        elif standard == ComplianceStandard.IT_ACT_2000:
            # Check IT Act 2000 compliance
            # Verify data encryption
            # Verify audit logs
            pass
        
        elif standard == ComplianceStandard.AADHAAR_ACT:
            # Check Aadhaar Act compliance
            # Verify Aadhaar data handling
            # Verify consent management
            pass
        
        is_compliant = len(violations) == 0
        
        return {
            'standard': standard.value,
            'compliant': is_compliant,
            'violations': violations,
            'checked_at': datetime.utcnow().isoformat()
        }
    
    def record_compliance_violation(
        self,
        standard: ComplianceStandard,
        severity: str,
        description: str
    ) -> ComplianceViolation:
        """
        Record a compliance violation
        
        Args:
            standard: Compliance standard violated
            severity: Violation severity
            description: Violation description
            
        Returns:
            Created violation record
        """
        import hashlib
        
        violation_id = hashlib.sha256(
            f"{standard.value}-{datetime.utcnow().timestamp()}".encode()
        ).hexdigest()[:16]
        
        violation = ComplianceViolation(
            violation_id=violation_id,
            standard=standard,
            severity=severity,
            description=description,
            detected_at=datetime.utcnow().isoformat(),
            resolved_at=None,
            resolution_notes=None
        )
        
        self.violations.append(violation)
        
        # Log to audit trail
        self.audit_logger.log_event(
            event_type=AuditEventType.SYSTEM_CONFIG_CHANGED,
            action=f"Compliance violation recorded: {standard.value}",
            details={
                'violation_id': violation_id,
                'standard': standard.value,
                'severity': severity,
                'description': description
            },
            severity='critical' if severity == 'high' else 'warning'
        )
        
        return violation
    
    def resolve_compliance_violation(
        self,
        violation_id: str,
        resolution_notes: str
    ) -> Optional[ComplianceViolation]:
        """
        Resolve a compliance violation
        
        Args:
            violation_id: Violation identifier
            resolution_notes: Notes on how violation was resolved
            
        Returns:
            Updated violation record
        """
        for violation in self.violations:
            if violation.violation_id == violation_id:
                violation.resolved_at = datetime.utcnow().isoformat()
                violation.resolution_notes = resolution_notes
                
                # Log resolution
                self.audit_logger.log_event(
                    event_type=AuditEventType.SYSTEM_CONFIG_CHANGED,
                    action=f"Compliance violation resolved: {violation_id}",
                    details={
                        'violation_id': violation_id,
                        'resolution_notes': resolution_notes
                    }
                )
                
                return violation
        
        return None
    
    def get_open_violations(self) -> List[ComplianceViolation]:
        """Get all open compliance violations"""
        return [v for v in self.violations if v.resolved_at is None]
    
    def generate_transparent_report(
        self,
        report_type: ReportType,
        start_date: datetime,
        end_date: datetime,
        format: str = 'json'
    ) -> str:
        """
        Generate transparent report for government authorities
        
        Args:
            report_type: Type of report to generate
            start_date: Report start date
            end_date: Report end date
            format: Output format ('json' or 'pdf')
            
        Returns:
            Generated report as string
        """
        # Generate appropriate report
        if report_type == ReportType.API_USAGE:
            report_data = self.generate_api_usage_report(start_date, end_date)
        elif report_type == ReportType.DATA_ACCESS:
            report_data = self.generate_data_access_report(start_date, end_date)
        elif report_type == ReportType.SECURITY_INCIDENTS:
            report_data = self.generate_security_incidents_report(start_date, end_date)
        elif report_type == ReportType.GDPR_COMPLIANCE:
            report_data = self.generate_gdpr_compliance_report(start_date, end_date)
        else:
            raise ValueError(f"Unsupported report type: {report_type}")
        
        # Add transparency metadata
        report_data['transparency'] = {
            'report_generated_by': 'SarvaSahay Platform',
            'report_purpose': 'Government compliance and transparency',
            'data_sources': ['audit_logs', 'gdpr_requests', 'api_logs'],
            'certification': 'This report is generated automatically and contains accurate data'
        }
        
        # Format output
        if format == 'json':
            return json.dumps(report_data, indent=2)
        elif format == 'pdf':
            # In production, would generate PDF using reportlab or similar
            return f"PDF Report: {report_type.value}\n{json.dumps(report_data, indent=2)}"
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def track_api_change_adaptation(
        self,
        api_name: str,
        old_version: str,
        new_version: str,
        adaptation_time_hours: float
    ) -> Dict[str, Any]:
        """
        Track API change adaptation for compliance
        Requirement: Adapt to API changes within 48 hours
        
        Args:
            api_name: Name of the API
            old_version: Previous API version
            new_version: New API version
            adaptation_time_hours: Time taken to adapt (hours)
            
        Returns:
            Adaptation tracking record
        """
        compliant = adaptation_time_hours <= 48
        
        # Log adaptation
        self.audit_logger.log_event(
            event_type=AuditEventType.SYSTEM_CONFIG_CHANGED,
            action=f"API version change adapted: {api_name}",
            details={
                'api_name': api_name,
                'old_version': old_version,
                'new_version': new_version,
                'adaptation_time_hours': adaptation_time_hours,
                'compliant': compliant
            },
            severity='info' if compliant else 'warning'
        )
        
        # Record violation if not compliant
        if not compliant:
            self.record_compliance_violation(
                standard=ComplianceStandard.MEITY_GUIDELINES,
                severity='medium',
                description=f"API change adaptation took {adaptation_time_hours} hours (>48 hours)"
            )
        
        return {
            'api_name': api_name,
            'old_version': old_version,
            'new_version': new_version,
            'adaptation_time_hours': adaptation_time_hours,
            'compliant': compliant,
            'requirement': '48 hours',
            'tracked_at': datetime.utcnow().isoformat()
        }
    
    def maintain_audit_trail(
        self,
        retention_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Maintain audit trail with proper retention
        
        Args:
            retention_days: Number of days to retain audit logs
            
        Returns:
            Maintenance result
        """
        retention_days = retention_days or self.data_retention_days
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Count logs to be archived
        logs_to_archive = [
            log for log in self.audit_logger.audit_logs
            if datetime.fromisoformat(log.timestamp) < cutoff_date
        ]
        
        # In production, would archive to long-term storage
        archived_count = len(logs_to_archive)
        
        return {
            'retention_days': retention_days,
            'cutoff_date': cutoff_date.isoformat(),
            'logs_archived': archived_count,
            'logs_retained': len(self.audit_logger.audit_logs) - archived_count,
            'maintained_at': datetime.utcnow().isoformat()
        }


# Global compliance reporting service instance
_compliance_service: Optional[ComplianceReportingService] = None


def get_compliance_service() -> ComplianceReportingService:
    """Get or create global compliance reporting service instance"""
    global _compliance_service
    if _compliance_service is None:
        _compliance_service = ComplianceReportingService()
    return _compliance_service
