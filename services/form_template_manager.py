"""
Form Template Management System
Manages form templates for 30+ government schemes with auto-population
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import json


class FieldType(str, Enum):
    """Form field types"""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    SELECT = "select"
    CHECKBOX = "checkbox"
    FILE = "file"
    TEXTAREA = "textarea"


class ValidationRule(str, Enum):
    """Field validation rules"""
    REQUIRED = "required"
    EMAIL = "email"
    PHONE = "phone"
    AADHAAR = "aadhaar"
    PAN = "pan"
    IFSC = "ifsc"
    PINCODE = "pincode"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"


class FormField:
    """Represents a single form field"""
    
    def __init__(
        self,
        field_id: str,
        label: str,
        field_type: FieldType,
        profile_mapping: Optional[str] = None,
        document_mapping: Optional[str] = None,
        validations: Optional[List[Dict[str, Any]]] = None,
        options: Optional[List[str]] = None,
        default_value: Optional[Any] = None,
        help_text: Optional[str] = None
    ):
        self.field_id = field_id
        self.label = label
        self.field_type = field_type
        self.profile_mapping = profile_mapping
        self.document_mapping = document_mapping
        self.validations = validations or []
        self.options = options or []
        self.default_value = default_value
        self.help_text = help_text
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert field to dictionary"""
        return {
            "fieldId": self.field_id,
            "label": self.label,
            "fieldType": self.field_type,
            "profileMapping": self.profile_mapping,
            "documentMapping": self.document_mapping,
            "validations": self.validations,
            "options": self.options,
            "defaultValue": self.default_value,
            "helpText": self.help_text
        }


class FormTemplate:
    """Represents a government scheme form template"""
    
    def __init__(
        self,
        template_id: str,
        scheme_id: str,
        scheme_name: str,
        version: str,
        fields: List[FormField],
        sections: Optional[List[Dict[str, Any]]] = None,
        instructions: Optional[str] = None
    ):
        self.template_id = template_id
        self.scheme_id = scheme_id
        self.scheme_name = scheme_name
        self.version = version
        self.fields = fields
        self.sections = sections or []
        self.instructions = instructions
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary"""
        return {
            "templateId": self.template_id,
            "schemeId": self.scheme_id,
            "schemeName": self.scheme_name,
            "version": self.version,
            "fields": [field.to_dict() for field in self.fields],
            "sections": self.sections,
            "instructions": self.instructions,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat()
        }


class FormTemplateManager:
    """
    Manages form templates for government schemes
    Handles auto-population, validation, and preview
    """
    
    def __init__(self):
        self.templates: Dict[str, FormTemplate] = {}
        self._initialize_default_templates()
    
    def _initialize_default_templates(self):
        """Initialize templates for major government schemes"""
        
        # PM-KISAN Template
        pm_kisan_fields = [
            FormField(
                "applicant_name",
                "Applicant Name",
                FieldType.TEXT,
                profile_mapping="demographics.name",
                validations=[{"rule": "required"}]
            ),
            FormField(
                "aadhaar_number",
                "Aadhaar Number",
                FieldType.TEXT,
                document_mapping="documents.aadhaar",
                validations=[
                    {"rule": "required"},
                    {"rule": "aadhaar"}
                ]
            ),
            FormField(
                "age",
                "Age",
                FieldType.NUMBER,
                profile_mapping="demographics.age",
                validations=[
                    {"rule": "required"},
                    {"rule": "min_value", "value": 18}
                ]
            ),
            FormField(
                "gender",
                "Gender",
                FieldType.SELECT,
                profile_mapping="demographics.gender",
                options=["male", "female", "other"],
                validations=[{"rule": "required"}]
            ),
            FormField(
                "land_ownership",
                "Land Ownership (acres)",
                FieldType.NUMBER,
                profile_mapping="economic.landOwnership",
                validations=[
                    {"rule": "required"},
                    {"rule": "min_value", "value": 0}
                ]
            ),
            FormField(
                "bank_account",
                "Bank Account Number",
                FieldType.TEXT,
                document_mapping="documents.bankAccount",
                validations=[
                    {"rule": "required"},
                    {"rule": "min_length", "value": 9},
                    {"rule": "max_length", "value": 18}
                ]
            ),
            FormField(
                "bank_ifsc",
                "Bank IFSC Code",
                FieldType.TEXT,
                document_mapping="documents.bankIfsc",
                validations=[
                    {"rule": "required"},
                    {"rule": "ifsc"}
                ]
            ),
            FormField(
                "state",
                "State",
                FieldType.TEXT,
                profile_mapping="location.state",
                validations=[{"rule": "required"}]
            ),
            FormField(
                "district",
                "District",
                FieldType.TEXT,
                profile_mapping="location.district",
                validations=[{"rule": "required"}]
            ),
            FormField(
                "village",
                "Village",
                FieldType.TEXT,
                profile_mapping="location.village",
                validations=[{"rule": "required"}]
            )
        ]
        
        pm_kisan_template = FormTemplate(
            template_id="PM-KISAN-FORM-V1",
            scheme_id="PM-KISAN",
            scheme_name="Pradhan Mantri Kisan Samman Nidhi",
            version="1.0",
            fields=pm_kisan_fields,
            sections=[
                {"title": "Personal Information", "fields": ["applicant_name", "aadhaar_number", "age", "gender"]},
                {"title": "Land Details", "fields": ["land_ownership"]},
                {"title": "Bank Details", "fields": ["bank_account", "bank_ifsc"]},
                {"title": "Location", "fields": ["state", "district", "village"]}
            ],
            instructions="Please fill all required fields. Ensure bank details are accurate for DBT transfer."
        )
        
        self.templates["PM-KISAN"] = pm_kisan_template
    
    def get_template(self, scheme_id: str) -> Optional[FormTemplate]:
        """Get form template for a scheme"""
        return self.templates.get(scheme_id)
    
    def add_template(self, template: FormTemplate) -> None:
        """Add a new form template"""
        self.templates[template.scheme_id] = template
    
    def auto_populate_form(
        self,
        scheme_id: str,
        user_profile: Dict[str, Any],
        document_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Auto-populate form using profile and document data
        
        Args:
            scheme_id: Government scheme identifier
            user_profile: User profile data
            document_data: Extracted document data
            
        Returns:
            Pre-filled form data
        """
        template = self.get_template(scheme_id)
        if not template:
            raise ValueError(f"Template not found for scheme: {scheme_id}")
        
        form_data = {}
        document_data = document_data or {}
        
        for field in template.fields:
            value = None
            
            # Try to get value from profile mapping
            if field.profile_mapping:
                value = self._get_nested_value(user_profile, field.profile_mapping)
            
            # Try to get value from document mapping if not found in profile
            if value is None and field.document_mapping:
                value = self._get_nested_value(document_data, field.document_mapping)
            
            # Use default value if still not found
            if value is None and field.default_value is not None:
                value = field.default_value
            
            form_data[field.field_id] = value
        
        return {
            "schemeId": scheme_id,
            "schemeName": template.scheme_name,
            "templateId": template.template_id,
            "formData": form_data,
            "populatedAt": datetime.utcnow().isoformat()
        }
    
    def validate_form(
        self,
        scheme_id: str,
        form_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate form data against template rules
        
        Args:
            scheme_id: Government scheme identifier
            form_data: Form data to validate
            
        Returns:
            Validation result with errors if any
        """
        template = self.get_template(scheme_id)
        if not template:
            raise ValueError(f"Template not found for scheme: {scheme_id}")
        
        errors = []
        warnings = []
        
        for field in template.fields:
            field_value = form_data.get(field.field_id)
            field_errors = self._validate_field(field, field_value)
            
            if field_errors:
                errors.extend([{
                    "fieldId": field.field_id,
                    "fieldLabel": field.label,
                    "error": error
                } for error in field_errors])
        
        is_valid = len(errors) == 0
        
        return {
            "isValid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "validatedAt": datetime.utcnow().isoformat()
        }
    
    def generate_preview(
        self,
        scheme_id: str,
        form_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate form preview for user review
        
        Args:
            scheme_id: Government scheme identifier
            form_data: Form data to preview
            
        Returns:
            Formatted preview data
        """
        template = self.get_template(scheme_id)
        if not template:
            raise ValueError(f"Template not found for scheme: {scheme_id}")
        
        preview_sections = []
        
        for section in template.sections:
            section_data = {
                "title": section["title"],
                "fields": []
            }
            
            for field_id in section["fields"]:
                field = next((f for f in template.fields if f.field_id == field_id), None)
                if field:
                    section_data["fields"].append({
                        "label": field.label,
                        "value": form_data.get(field_id, "Not provided"),
                        "fieldType": field.field_type
                    })
            
            preview_sections.append(section_data)
        
        return {
            "schemeId": scheme_id,
            "schemeName": template.scheme_name,
            "sections": preview_sections,
            "instructions": template.instructions,
            "generatedAt": datetime.utcnow().isoformat()
        }
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value from dictionary using dot notation"""
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
            
            if value is None:
                return None
        
        return value
    
    def _validate_field(
        self,
        field: FormField,
        value: Any
    ) -> List[str]:
        """Validate a single field value"""
        errors = []
        
        for validation in field.validations:
            rule = validation.get("rule")
            
            if rule == "required":
                if value is None or value == "":
                    errors.append(f"{field.label} is required")
            
            elif rule == "min_length" and value:
                min_len = validation.get("value", 0)
                if len(str(value)) < min_len:
                    errors.append(f"{field.label} must be at least {min_len} characters")
            
            elif rule == "max_length" and value:
                max_len = validation.get("value", 0)
                if len(str(value)) > max_len:
                    errors.append(f"{field.label} must not exceed {max_len} characters")
            
            elif rule == "min_value" and value is not None:
                min_val = validation.get("value", 0)
                if float(value) < min_val:
                    errors.append(f"{field.label} must be at least {min_val}")
            
            elif rule == "max_value" and value is not None:
                max_val = validation.get("value", 0)
                if float(value) > max_val:
                    errors.append(f"{field.label} must not exceed {max_val}")
            
            elif rule == "aadhaar" and value:
                if not self._validate_aadhaar(str(value)):
                    errors.append(f"{field.label} must be a valid 12-digit Aadhaar number")
            
            elif rule == "pan" and value:
                if not self._validate_pan(str(value)):
                    errors.append(f"{field.label} must be a valid PAN (e.g., ABCDE1234F)")
            
            elif rule == "ifsc" and value:
                if not self._validate_ifsc(str(value)):
                    errors.append(f"{field.label} must be a valid IFSC code")
        
        return errors
    
    def _validate_aadhaar(self, value: str) -> bool:
        """Validate Aadhaar number format"""
        import re
        return bool(re.match(r'^\d{12}$', value))
    
    def _validate_pan(self, value: str) -> bool:
        """Validate PAN format"""
        import re
        return bool(re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', value))
    
    def _validate_ifsc(self, value: str) -> bool:
        """Validate IFSC code format"""
        import re
        return bool(re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', value))
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available form templates"""
        return [
            {
                "templateId": template.template_id,
                "schemeId": template.scheme_id,
                "schemeName": template.scheme_name,
                "version": template.version,
                "fieldCount": len(template.fields)
            }
            for template in self.templates.values()
        ]
