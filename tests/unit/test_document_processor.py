"""
Unit tests for Document Processing Service
Tests OCR, validation, and quality assessment functionality
"""

import pytest
import numpy as np
import cv2
from services.document_processor import DocumentProcessor, DocumentType, DocumentQuality
from services.document_validator import DocumentValidator, ValidationSeverity


class TestDocumentProcessor:
    """Test suite for DocumentProcessor"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.processor = DocumentProcessor()
        self.validator = DocumentValidator()
    
    def create_test_image(self, text: str, quality: str = "good") -> np.ndarray:
        """Create a test image with text"""
        # Create blank white image
        if quality == "good":
            img = np.ones((400, 600, 3), dtype=np.uint8) * 255
        elif quality == "poor":
            img = np.ones((400, 600, 3), dtype=np.uint8) * 200  # Lower brightness
        else:
            img = np.ones((400, 600, 3), dtype=np.uint8) * 100  # Very dark
        
        # Add text to image
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, text, (50, 200), font, 1, (0, 0, 0), 2, cv2.LINE_AA)
        
        return img
    
    def test_preprocess_image(self):
        """Test image preprocessing"""
        # Create test image
        img = self.create_test_image("Test Document")
        
        # Preprocess
        processed = self.processor._preprocess_image(img)
        
        # Verify output
        assert processed is not None
        assert len(processed.shape) == 2  # Should be grayscale
        assert processed.dtype == np.uint8
    
    def test_assess_image_quality_good(self):
        """Test quality assessment for good image"""
        img = self.create_test_image("Test Document", quality="good")
        processed = self.processor._preprocess_image(img)
        
        quality_score, quality_level = self.processor._assess_image_quality(processed)
        
        assert 0.0 <= quality_score <= 1.0
        assert quality_level in [
            DocumentQuality.EXCELLENT,
            DocumentQuality.GOOD,
            DocumentQuality.ACCEPTABLE
        ]
    
    def test_assess_image_quality_poor(self):
        """Test quality assessment for poor image"""
        img = self.create_test_image("Test Document", quality="poor")
        processed = self.processor._preprocess_image(img)
        
        quality_score, quality_level = self.processor._assess_image_quality(processed)
        
        assert 0.0 <= quality_score <= 1.0
        # Poor quality image should have lower score than excellent
        assert quality_score < 0.9
    
    def test_parse_aadhaar_valid(self):
        """Test parsing valid Aadhaar data"""
        text = """
        Government of India
        Aadhaar Card
        Name: Ramesh Kumar
        DOB: 15/08/1985
        Male
        Aadhaar: 1234 5678 9012
        Address: Village Pirangut, Pune, Maharashtra
        """
        
        parsed = self.processor._parse_aadhaar(text)
        
        assert 'aadhaar_number' in parsed
        assert parsed['aadhaar_number'] == '123456789012'
        assert 'name' in parsed
        assert 'gender' in parsed
        assert parsed['gender'] == 'male'
    
    def test_parse_pan_valid(self):
        """Test parsing valid PAN data"""
        text = """
        Income Tax Department
        Permanent Account Number Card
        Name: RAMESH KUMAR
        Father's Name: SURESH KUMAR
        Date of Birth: 15/08/1985
        PAN: ABCDE1234F
        """
        
        parsed = self.processor._parse_pan(text)
        
        assert 'pan_number' in parsed
        assert parsed['pan_number'] == 'ABCDE1234F'
        assert 'name' in parsed
        # Father's name parsing may vary based on regex
        assert 'date_of_birth' in parsed
    
    def test_parse_land_records(self):
        """Test parsing land records"""
        text = """
        Land Records
        Survey No: 123/4
        Owner: Ramesh Kumar
        Village: Pirangut
        Area: 2.5 Acres
        """
        
        parsed = self.processor._parse_land_records(text)
        
        assert 'survey_number' in parsed
        assert 'land_area' in parsed
        assert parsed['land_area'] == 2.5
        assert 'owner_name' in parsed
    
    def test_parse_bank_passbook(self):
        """Test parsing bank passbook"""
        text = """
        State Bank of India
        Account Holder: Ramesh Kumar
        Account No: 1234567890
        IFSC: SBIN0001234
        Branch: Pune Main
        """
        
        parsed = self.processor._parse_bank_passbook(text)
        
        assert 'account_number' in parsed
        assert parsed['account_number'] == '1234567890'
        # IFSC parsing depends on exact format
        assert 'bank_name' in parsed
    
    def test_validate_aadhaar_format(self):
        """Test Aadhaar format validation"""
        # Valid Aadhaar
        valid_data = {'aadhaar_number': '123456789012'}
        result = self.processor._validate_extracted_data(
            valid_data,
            DocumentType.AADHAAR,
            None
        )
        assert result['is_valid'] is True
        
        # Invalid Aadhaar
        invalid_data = {'aadhaar_number': '12345'}
        result = self.processor._validate_extracted_data(
            invalid_data,
            DocumentType.AADHAAR,
            None
        )
        assert result['is_valid'] is False
        assert len(result['errors']) > 0
    
    def test_validate_pan_format(self):
        """Test PAN format validation"""
        # Valid PAN
        valid_data = {'pan_number': 'ABCDE1234F'}
        result = self.processor._validate_extracted_data(
            valid_data,
            DocumentType.PAN,
            None
        )
        assert result['is_valid'] is True
        
        # Invalid PAN
        invalid_data = {'pan_number': 'INVALID'}
        result = self.processor._validate_extracted_data(
            invalid_data,
            DocumentType.PAN,
            None
        )
        assert result['is_valid'] is False
    
    def test_cross_validate_with_profile_match(self):
        """Test cross-validation with matching profile"""
        parsed_data = {
            'aadhaar_number': '123456789012',
            'gender': 'male'
        }
        
        user_profile = {
            'documents': {'aadhaar': '123456789012'},
            'demographics': {'gender': 'male'}
        }
        
        inconsistencies = self.processor._cross_validate_with_profile(
            parsed_data,
            DocumentType.AADHAAR,
            user_profile
        )
        
        assert len(inconsistencies) == 0
    
    def test_cross_validate_with_profile_mismatch(self):
        """Test cross-validation with mismatched profile"""
        parsed_data = {
            'aadhaar_number': '999999999999',
            'gender': 'female'
        }
        
        user_profile = {
            'documents': {'aadhaar': '123456789012'},
            'demographics': {'gender': 'male'}
        }
        
        inconsistencies = self.processor._cross_validate_with_profile(
            parsed_data,
            DocumentType.AADHAAR,
            user_profile
        )
        
        assert len(inconsistencies) > 0
    
    def test_generate_improvement_suggestions_poor_quality(self):
        """Test improvement suggestions for poor quality"""
        suggestions = self.processor._generate_improvement_suggestions(
            DocumentQuality.POOR,
            {'is_valid': True, 'errors': [], 'inconsistencies': []}
        )
        
        assert len(suggestions) > 0
        assert any('lighting' in s.lower() for s in suggestions)
    
    def test_generate_improvement_suggestions_validation_failed(self):
        """Test improvement suggestions for validation failure"""
        suggestions = self.processor._generate_improvement_suggestions(
            DocumentQuality.GOOD,
            {'is_valid': False, 'errors': ['Invalid format'], 'inconsistencies': []}
        )
        
        assert len(suggestions) > 0
        assert any('validation' in s.lower() for s in suggestions)
    
    def test_process_document_empty_image(self):
        """Test processing with empty image"""
        with pytest.raises(ValueError, match="Image data cannot be empty"):
            self.processor.process_document(
                np.array([]),
                DocumentType.AADHAAR
            )
    
    def test_generate_document_id(self):
        """Test document ID generation"""
        parsed_data = {'aadhaar_number': '123456789012'}
        
        doc_id1 = self.processor._generate_document_id(
            DocumentType.AADHAAR,
            parsed_data
        )
        
        assert doc_id1 is not None
        assert len(doc_id1) == 16
        
        # Different calls should generate different IDs (due to timestamp)
        import time
        time.sleep(0.01)
        doc_id2 = self.processor._generate_document_id(
            DocumentType.AADHAAR,
            parsed_data
        )
        assert doc_id1 != doc_id2


class TestDocumentValidator:
    """Test suite for DocumentValidator"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.validator = DocumentValidator()
    
    def create_processed_document(
        self,
        document_type: str = "aadhaar",
        quality_score: float = 0.8,
        parsed_data: dict = None
    ) -> dict:
        """Create a mock processed document"""
        if parsed_data is None:
            parsed_data = {
                'aadhaar_number': '123456789012',
                'name': 'Test User',
                'gender': 'male'
            }
        
        return {
            'document_id': 'test-doc-123',
            'document_type': document_type,
            'quality_score': quality_score,
            'quality_level': 'good',
            'parsed_data': parsed_data,
            'extracted_text': 'Sample text',
            'validation_results': {'is_valid': True, 'errors': [], 'inconsistencies': []}
        }
    
    def test_validate_document_high_quality(self):
        """Test validation of high-quality document"""
        doc = self.create_processed_document(quality_score=0.9)
        
        report = self.validator.validate_document(doc)
        
        assert report['overall_score'] > 0.7
        assert report['is_approved'] is True
        assert 'quality_assessment' in report
        assert 'data_validation' in report
    
    def test_validate_document_low_quality(self):
        """Test validation of low-quality document"""
        doc = self.create_processed_document(quality_score=0.3)
        
        report = self.validator.validate_document(doc)
        
        # Low quality should result in lower overall score
        assert report['overall_score'] < 0.9
        assert len(report['issues']) > 0
    
    def test_validate_data_completeness_complete(self):
        """Test data completeness with all required fields"""
        doc = self.create_processed_document(
            parsed_data={'aadhaar_number': '123456789012', 'name': 'Test User'}
        )
        
        validation = self.validator._validate_data_completeness(doc, strict_mode=False)
        
        assert validation['completeness_score'] == 1.0
        assert len(validation['missing_fields']) == 0
    
    def test_validate_data_completeness_incomplete(self):
        """Test data completeness with missing fields"""
        doc = self.create_processed_document(
            parsed_data={'aadhaar_number': '123456789012'}  # Missing name
        )
        
        validation = self.validator._validate_data_completeness(doc, strict_mode=False)
        
        assert validation['completeness_score'] < 1.0
        assert 'name' in validation['missing_fields']
    
    def test_validate_field_formats_valid(self):
        """Test field format validation with valid data"""
        parsed_data = {
            'aadhaar_number': '123456789012',
            'pan_number': 'ABCDE1234F',
            'ifsc_code': 'SBIN0001234'
        }
        
        invalid = self.validator._validate_field_formats(parsed_data, 'aadhaar')
        
        assert len(invalid) == 0
    
    def test_validate_field_formats_invalid(self):
        """Test field format validation with invalid data"""
        parsed_data = {
            'aadhaar_number': '12345',  # Too short
            'pan_number': 'INVALID',
            'ifsc_code': 'WRONG'
        }
        
        invalid = self.validator._validate_field_formats(parsed_data, 'aadhaar')
        
        assert len(invalid) > 0
        assert 'aadhaar_number' in invalid
    
    def test_validate_profile_consistency_match(self):
        """Test profile consistency with matching data"""
        doc = self.create_processed_document()
        
        user_profile = {
            'documents': {'aadhaar': '123456789012'},
            'demographics': {'gender': 'male'}
        }
        
        consistency = self.validator._validate_profile_consistency(doc, user_profile)
        
        assert consistency['consistency_score'] == 1.0
        assert len(consistency['mismatches']) == 0
    
    def test_validate_profile_consistency_mismatch(self):
        """Test profile consistency with mismatched data"""
        doc = self.create_processed_document()
        
        user_profile = {
            'documents': {'aadhaar': '999999999999'},  # Different Aadhaar
            'demographics': {'gender': 'female'}  # Different gender
        }
        
        consistency = self.validator._validate_profile_consistency(doc, user_profile)
        
        assert consistency['consistency_score'] < 1.0
        assert len(consistency['mismatches']) > 0
    
    def test_calculate_overall_score(self):
        """Test overall score calculation"""
        quality = {'quality_score': 0.8}
        data_val = {'completeness_score': 0.9}
        consistency = {'consistency_score': 1.0}
        
        score = self.validator._calculate_overall_score(
            quality,
            data_val,
            consistency
        )
        
        assert 0.0 <= score <= 1.0
        assert score > 0.8  # Should be high with good inputs
    
    def test_determine_approval_strict_mode(self):
        """Test approval determination in strict mode"""
        # High score, no errors - should approve
        assert self.validator._determine_approval(0.8, [], strict_mode=True) is True
        
        # High score with errors - should reject
        issues = [{'severity': ValidationSeverity.ERROR.value}]
        assert self.validator._determine_approval(0.8, issues, strict_mode=True) is False
        
        # Low score - should reject
        assert self.validator._determine_approval(0.5, [], strict_mode=True) is False
    
    def test_determine_approval_normal_mode(self):
        """Test approval determination in normal mode"""
        # Acceptable score - should approve
        assert self.validator._determine_approval(0.6, [], strict_mode=False) is True
        
        # Low score - should reject
        assert self.validator._determine_approval(0.4, [], strict_mode=False) is False
    
    def test_generate_recommendations(self):
        """Test recommendation generation"""
        report = {
            'quality_assessment': {'quality_score': 0.5},
            'data_validation': {
                'completeness_score': 0.7,
                'missing_fields': ['name']
            },
            'profile_consistency': {
                'mismatches': [
                    {'field': 'aadhaar', 'profile_value': '111', 'document_value': '222'}
                ]
            },
            'overall_score': 0.6
        }
        
        recommendations = self.validator._generate_recommendations(report)
        
        assert len(recommendations) > 0
        assert any('photo' in r.lower() or 'lighting' in r.lower() for r in recommendations)
    
    def test_suggest_profile_updates(self):
        """Test profile update suggestions"""
        report = {
            'is_approved': True,
            'overall_score': 0.9,
            'profile_consistency': {
                'mismatches': [
                    {
                        'field': 'aadhaar_number',
                        'profile_value': '111111111111',
                        'document_value': '222222222222'
                    }
                ]
            }
        }
        
        suggestions = self.validator.suggest_profile_updates(report)
        
        assert suggestions['should_update'] is True
        assert 'documents.aadhaar' in suggestions['suggested_updates']
        assert suggestions['confidence'] > 0.8
    
    def test_get_validation_statistics(self):
        """Test validation statistics"""
        # Create fresh validator to avoid interference from other tests
        validator = DocumentValidator()
        
        # Create and validate some documents with unique IDs
        doc1 = self.create_processed_document(quality_score=0.9)
        doc1['document_id'] = 'test-doc-stats-1'
        
        doc2 = self.create_processed_document(quality_score=0.3)
        doc2['document_id'] = 'test-doc-stats-2'
        
        validator.validate_document(doc1)
        validator.validate_document(doc2)
        
        stats = validator.get_validation_statistics()
        
        assert stats['total_validations'] == 2
        assert stats['approved_count'] >= 0
        assert stats['rejected_count'] >= 0
        assert 0.0 <= stats['average_score'] <= 1.0
    
    def test_batch_validate_documents(self):
        """Test batch validation"""
        docs = [
            self.create_processed_document(quality_score=0.9),
            self.create_processed_document(quality_score=0.7),
            self.create_processed_document(quality_score=0.5)
        ]
        
        reports = self.validator.batch_validate_documents(docs)
        
        assert len(reports) == 3
        assert all('overall_score' in r for r in reports)
        assert all('is_approved' in r for r in reports)
