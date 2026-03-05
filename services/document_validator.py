"""
SarvaSahay Document Validation Service
Advanced validation and quality assessment for processed documents
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from datetime import datetime
import re


class ValidationSeverity(str, Enum):
    """Validation issue severity levels"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationRule:
    """Base class for validation rules"""
    
    def __init__(self, name: str, severity: ValidationSeverity):
        self.name = name
        self.severity = severity
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate data against rule
        Returns (is_valid, error_message)
        """
        raise NotImplementedError


class DocumentValidator:
    """
    Advanced document validation and quality assessment
    Cross-validates extracted data with user profiles
    """
    
    def __init__(self):
        self.validation_history = {}
        self.quality_thresholds = {
            "excellent": 0.8,
            "good": 0.6,
            "acceptable": 0.4,
            "poor": 0.2
        }
    
    def validate_document(
        self,
        processed_document: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]] = None,
        strict_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Comprehensive document validation
        
        Args:
            processed_document: Document data from DocumentProcessor
            user_profile: User profile for cross-validation
            strict_mode: If True, apply stricter validation rules
            
        Returns:
            Validation report with scores, issues, and recommendations
        """
        validation_report = {
            "document_id": processed_document.get("document_id"),
            "document_type": processed_document.get("document_type"),
            "validation_timestamp": datetime.utcnow().isoformat(),
            "overall_score": 0.0,
            "quality_assessment": {},
            "data_validation": {},
            "profile_consistency": {},
            "issues": [],
            "recommendations": [],
            "is_approved": False
        }
        
        # 1. Assess document quality
        quality_assessment = self._assess_document_quality(processed_document)
        validation_report["quality_assessment"] = quality_assessment
        
        # 2. Validate extracted data completeness and format
        data_validation = self._validate_data_completeness(
            processed_document,
            strict_mode
        )
        validation_report["data_validation"] = data_validation
        
        # 3. Cross-validate with user profile
        if user_profile:
            profile_consistency = self._validate_profile_consistency(
                processed_document,
                user_profile
            )
            validation_report["profile_consistency"] = profile_consistency
        
        # 4. Calculate overall validation score
        overall_score = self._calculate_overall_score(
            quality_assessment,
            data_validation,
            validation_report.get("profile_consistency", {})
        )
        validation_report["overall_score"] = overall_score
        
        # 5. Collect all issues
        validation_report["issues"] = self._collect_issues(
            quality_assessment,
            data_validation,
            validation_report.get("profile_consistency", {})
        )
        
        # 6. Generate recommendations
        validation_report["recommendations"] = self._generate_recommendations(
            validation_report
        )
        
        # 7. Determine approval status
        validation_report["is_approved"] = self._determine_approval(
            overall_score,
            validation_report["issues"],
            strict_mode
        )
        
        # Store validation history
        self.validation_history[processed_document.get("document_id")] = validation_report
        
        return validation_report
    
    def _assess_document_quality(
        self,
        processed_document: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess document image quality"""
        quality_score = processed_document.get("quality_score", 0.0)
        quality_level = processed_document.get("quality_level", "unknown")
        
        assessment = {
            "quality_score": quality_score,
            "quality_level": quality_level,
            "is_acceptable": quality_score >= self.quality_thresholds["acceptable"],
            "metrics": {
                "sharpness": "calculated",
                "brightness": "calculated",
                "contrast": "calculated"
            },
            "issues": []
        }
        
        # Identify quality issues
        if quality_score < self.quality_thresholds["acceptable"]:
            assessment["issues"].append({
                "severity": ValidationSeverity.ERROR.value,
                "message": f"Image quality too low ({quality_level})",
                "suggestion": "Retake photo in better lighting conditions"
            })
        elif quality_score < self.quality_thresholds["good"]:
            assessment["issues"].append({
                "severity": ValidationSeverity.WARNING.value,
                "message": f"Image quality could be improved ({quality_level})",
                "suggestion": "Consider retaking for better accuracy"
            })
        
        return assessment
    
    def _validate_data_completeness(
        self,
        processed_document: Dict[str, Any],
        strict_mode: bool
    ) -> Dict[str, Any]:
        """Validate completeness and format of extracted data"""
        document_type = processed_document.get("document_type")
        parsed_data = processed_document.get("parsed_data", {})
        
        validation = {
            "completeness_score": 0.0,
            "required_fields_present": [],
            "missing_fields": [],
            "invalid_fields": [],
            "issues": []
        }
        
        # Define required fields per document type
        required_fields = self._get_required_fields(document_type)
        
        # Check field presence
        present_fields = []
        missing_fields = []
        
        for field in required_fields:
            if field in parsed_data and parsed_data[field]:
                present_fields.append(field)
            else:
                missing_fields.append(field)
        
        validation["required_fields_present"] = present_fields
        validation["missing_fields"] = missing_fields
        
        # Calculate completeness score
        if required_fields:
            validation["completeness_score"] = len(present_fields) / len(required_fields)
        
        # Validate field formats
        invalid_fields = self._validate_field_formats(parsed_data, document_type)
        validation["invalid_fields"] = invalid_fields
        
        # Generate issues
        if missing_fields:
            severity = ValidationSeverity.ERROR if strict_mode else ValidationSeverity.WARNING
            validation["issues"].append({
                "severity": severity.value,
                "message": f"Missing required fields: {', '.join(missing_fields)}",
                "suggestion": "Ensure document is fully visible and clear"
            })
        
        if invalid_fields:
            validation["issues"].append({
                "severity": ValidationSeverity.ERROR.value,
                "message": f"Invalid field formats: {', '.join(invalid_fields)}",
                "suggestion": "Verify document authenticity"
            })
        
        return validation
    
    def _get_required_fields(self, document_type: str) -> List[str]:
        """Get required fields for document type"""
        required_fields_map = {
            "aadhaar": ["aadhaar_number", "name"],
            "pan": ["pan_number", "name"],
            "land_records": ["survey_number", "land_area", "owner_name"],
            "bank_passbook": ["account_number", "ifsc_code", "account_holder_name"],
            "ration_card": ["ration_card_number", "head_of_family"],
            "voter_id": ["voter_id_number", "name"]
        }
        
        return required_fields_map.get(document_type, [])
    
    def _validate_field_formats(
        self,
        parsed_data: Dict[str, Any],
        document_type: str
    ) -> List[str]:
        """Validate format of extracted fields"""
        invalid_fields = []
        
        # Aadhaar validation
        if 'aadhaar_number' in parsed_data:
            if not re.match(r'^\d{12}$', str(parsed_data['aadhaar_number'])):
                invalid_fields.append('aadhaar_number')
        
        # PAN validation
        if 'pan_number' in parsed_data:
            if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', parsed_data['pan_number']):
                invalid_fields.append('pan_number')
        
        # IFSC validation
        if 'ifsc_code' in parsed_data:
            if not re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', parsed_data['ifsc_code']):
                invalid_fields.append('ifsc_code')
        
        # Account number validation
        if 'account_number' in parsed_data:
            account = str(parsed_data['account_number'])
            if not (9 <= len(account) <= 18 and account.isdigit()):
                invalid_fields.append('account_number')
        
        # Land area validation
        if 'land_area' in parsed_data:
            try:
                area = float(parsed_data['land_area'])
                if area <= 0 or area > 1000:  # Reasonable limits
                    invalid_fields.append('land_area')
            except (ValueError, TypeError):
                invalid_fields.append('land_area')
        
        return invalid_fields
    
    def _validate_profile_consistency(
        self,
        processed_document: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Cross-validate document data with user profile"""
        document_type = processed_document.get("document_type")
        parsed_data = processed_document.get("parsed_data", {})
        
        consistency = {
            "consistency_score": 1.0,
            "matches": [],
            "mismatches": [],
            "issues": []
        }
        
        mismatches = []
        matches = []
        
        # Validate Aadhaar
        if document_type == "aadhaar":
            if 'aadhaar_number' in parsed_data:
                profile_aadhaar = user_profile.get('documents', {}).get('aadhaar')
                if profile_aadhaar:
                    if profile_aadhaar == parsed_data['aadhaar_number']:
                        matches.append("aadhaar_number")
                    else:
                        mismatches.append({
                            "field": "aadhaar_number",
                            "profile_value": profile_aadhaar,
                            "document_value": parsed_data['aadhaar_number']
                        })
            
            # Validate gender
            if 'gender' in parsed_data:
                profile_gender = user_profile.get('demographics', {}).get('gender')
                if profile_gender:
                    if profile_gender == parsed_data['gender']:
                        matches.append("gender")
                    else:
                        mismatches.append({
                            "field": "gender",
                            "profile_value": profile_gender,
                            "document_value": parsed_data['gender']
                        })
        
        # Validate PAN
        elif document_type == "pan":
            if 'pan_number' in parsed_data:
                profile_pan = user_profile.get('documents', {}).get('pan')
                if profile_pan:
                    if profile_pan == parsed_data['pan_number']:
                        matches.append("pan_number")
                    else:
                        mismatches.append({
                            "field": "pan_number",
                            "profile_value": profile_pan,
                            "document_value": parsed_data['pan_number']
                        })
        
        # Validate land records
        elif document_type == "land_records":
            if 'land_area' in parsed_data:
                profile_land = user_profile.get('economic', {}).get('land_ownership')
                if profile_land:
                    doc_land = float(parsed_data['land_area'])
                    
                    # Convert to acres if needed
                    if parsed_data.get('land_unit') in ['hectare', 'hectares']:
                        doc_land *= 2.47105
                    
                    # Allow 10% tolerance
                    tolerance = profile_land * 0.1
                    if abs(profile_land - doc_land) <= tolerance:
                        matches.append("land_area")
                    else:
                        mismatches.append({
                            "field": "land_area",
                            "profile_value": f"{profile_land} acres",
                            "document_value": f"{doc_land} acres"
                        })
        
        # Validate bank details
        elif document_type == "bank_passbook":
            if 'account_number' in parsed_data:
                profile_account = user_profile.get('documents', {}).get('bank_account')
                if profile_account:
                    if profile_account == parsed_data['account_number']:
                        matches.append("account_number")
                    else:
                        mismatches.append({
                            "field": "account_number",
                            "profile_value": profile_account,
                            "document_value": parsed_data['account_number']
                        })
            
            if 'ifsc_code' in parsed_data:
                profile_ifsc = user_profile.get('documents', {}).get('bank_ifsc')
                if profile_ifsc:
                    if profile_ifsc == parsed_data['ifsc_code']:
                        matches.append("ifsc_code")
                    else:
                        mismatches.append({
                            "field": "ifsc_code",
                            "profile_value": profile_ifsc,
                            "document_value": parsed_data['ifsc_code']
                        })
        
        consistency["matches"] = matches
        consistency["mismatches"] = mismatches
        
        # Calculate consistency score
        total_checks = len(matches) + len(mismatches)
        if total_checks > 0:
            consistency["consistency_score"] = len(matches) / total_checks
        
        # Generate issues for mismatches
        if mismatches:
            consistency["issues"].append({
                "severity": ValidationSeverity.WARNING.value,
                "message": f"Found {len(mismatches)} data inconsistencies with profile",
                "details": mismatches,
                "suggestion": "Review and update profile if document is correct"
            })
        
        return consistency

    
    def _calculate_overall_score(
        self,
        quality_assessment: Dict[str, Any],
        data_validation: Dict[str, Any],
        profile_consistency: Dict[str, Any]
    ) -> float:
        """Calculate overall validation score (0-1)"""
        # Weighted scoring
        quality_weight = 0.3
        completeness_weight = 0.4
        consistency_weight = 0.3
        
        quality_score = quality_assessment.get("quality_score", 0.0)
        completeness_score = data_validation.get("completeness_score", 0.0)
        consistency_score = profile_consistency.get("consistency_score", 1.0) if profile_consistency else 1.0
        
        overall = (
            quality_weight * quality_score +
            completeness_weight * completeness_score +
            consistency_weight * consistency_score
        )
        
        return round(overall, 3)
    
    def _collect_issues(
        self,
        quality_assessment: Dict[str, Any],
        data_validation: Dict[str, Any],
        profile_consistency: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Collect all validation issues"""
        issues = []
        
        # Quality issues
        issues.extend(quality_assessment.get("issues", []))
        
        # Data validation issues
        issues.extend(data_validation.get("issues", []))
        
        # Profile consistency issues
        if profile_consistency:
            issues.extend(profile_consistency.get("issues", []))
        
        # Sort by severity
        severity_order = {
            ValidationSeverity.CRITICAL.value: 0,
            ValidationSeverity.ERROR.value: 1,
            ValidationSeverity.WARNING.value: 2,
            ValidationSeverity.INFO.value: 3
        }
        
        issues.sort(key=lambda x: severity_order.get(x.get("severity"), 999))
        
        return issues
    
    def _generate_recommendations(
        self,
        validation_report: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        quality_score = validation_report["quality_assessment"]["quality_score"]
        completeness_score = validation_report["data_validation"]["completeness_score"]
        overall_score = validation_report["overall_score"]
        
        # Quality recommendations
        if quality_score < self.quality_thresholds["good"]:
            recommendations.append(
                "📸 Retake photo in better lighting for improved accuracy"
            )
            recommendations.append(
                "💡 Ensure document is flat and all corners are visible"
            )
            recommendations.append(
                "🔆 Avoid shadows and glare on the document"
            )
        
        # Completeness recommendations
        if completeness_score < 0.8:
            missing_fields = validation_report["data_validation"]["missing_fields"]
            if missing_fields:
                recommendations.append(
                    f"📋 Missing fields detected: {', '.join(missing_fields)}"
                )
                recommendations.append(
                    "✓ Verify document is complete and not damaged"
                )
        
        # Consistency recommendations
        if validation_report.get("profile_consistency"):
            mismatches = validation_report["profile_consistency"].get("mismatches", [])
            if mismatches:
                recommendations.append(
                    "⚠️ Data inconsistencies found with your profile"
                )
                recommendations.append(
                    "🔄 Review and update your profile if document is correct"
                )
                for mismatch in mismatches:
                    field = mismatch["field"]
                    recommendations.append(
                        f"   • {field}: Profile shows '{mismatch['profile_value']}', "
                        f"document shows '{mismatch['document_value']}'"
                    )
        
        # Overall recommendations
        if overall_score >= 0.8:
            recommendations.append("✅ Document validation passed - ready for use")
        elif overall_score >= 0.6:
            recommendations.append("⚡ Document acceptable but improvements recommended")
        else:
            recommendations.append("❌ Document needs improvement before use")
            recommendations.append("🔄 Please address the issues listed above")
        
        return recommendations
    
    def _determine_approval(
        self,
        overall_score: float,
        issues: List[Dict[str, Any]],
        strict_mode: bool
    ) -> bool:
        """Determine if document is approved for use"""
        # Check for critical or error issues
        has_critical = any(
            issue.get("severity") == ValidationSeverity.CRITICAL.value 
            for issue in issues
        )
        has_errors = any(
            issue.get("severity") == ValidationSeverity.ERROR.value 
            for issue in issues
        )
        
        if has_critical:
            return False
        
        if strict_mode:
            # Strict mode: no errors allowed, score must be >= 0.7
            return not has_errors and overall_score >= 0.7
        else:
            # Normal mode: score must be >= 0.5
            return overall_score >= 0.5
    
    def get_validation_report(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve validation report by document ID"""
        return self.validation_history.get(document_id)
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get overall validation statistics"""
        if not self.validation_history:
            return {
                "total_validations": 0,
                "approved_count": 0,
                "rejected_count": 0,
                "average_score": 0.0
            }
        
        total = len(self.validation_history)
        approved = sum(
            1 for report in self.validation_history.values() 
            if report["is_approved"]
        )
        rejected = total - approved
        
        avg_score = sum(
            report["overall_score"] 
            for report in self.validation_history.values()
        ) / total
        
        return {
            "total_validations": total,
            "approved_count": approved,
            "rejected_count": rejected,
            "approval_rate": approved / total if total > 0 else 0.0,
            "average_score": round(avg_score, 3)
        }
    
    def batch_validate_documents(
        self,
        processed_documents: List[Dict[str, Any]],
        user_profile: Optional[Dict[str, Any]] = None,
        strict_mode: bool = False
    ) -> List[Dict[str, Any]]:
        """Validate multiple documents in batch"""
        validation_reports = []
        
        for document in processed_documents:
            report = self.validate_document(document, user_profile, strict_mode)
            validation_reports.append(report)
        
        return validation_reports
    
    def suggest_profile_updates(
        self,
        validation_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Suggest profile updates based on document validation"""
        suggestions = {
            "should_update": False,
            "suggested_updates": {},
            "confidence": 0.0
        }
        
        # Only suggest updates if document is high quality and approved
        if (validation_report["is_approved"] and 
            validation_report["overall_score"] >= 0.8):
            
            profile_consistency = validation_report.get("profile_consistency", {})
            mismatches = profile_consistency.get("mismatches", [])
            
            if mismatches:
                suggestions["should_update"] = True
                
                for mismatch in mismatches:
                    field = mismatch["field"]
                    document_value = mismatch["document_value"]
                    
                    # Map document fields to profile fields
                    if field == "aadhaar_number":
                        suggestions["suggested_updates"]["documents.aadhaar"] = document_value
                    elif field == "pan_number":
                        suggestions["suggested_updates"]["documents.pan"] = document_value
                    elif field == "gender":
                        suggestions["suggested_updates"]["demographics.gender"] = document_value
                    elif field == "land_area":
                        suggestions["suggested_updates"]["economic.land_ownership"] = document_value
                    elif field == "account_number":
                        suggestions["suggested_updates"]["documents.bank_account"] = document_value
                    elif field == "ifsc_code":
                        suggestions["suggested_updates"]["documents.bank_ifsc"] = document_value
                
                # Confidence based on document quality
                suggestions["confidence"] = validation_report["overall_score"]
        
        return suggestions
