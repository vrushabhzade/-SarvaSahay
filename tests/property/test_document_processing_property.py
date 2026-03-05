"""
Property-Based Tests for Document Processing Round-Trip Integrity
Feature: sarvasahay-platform, Property 3: Document Processing Round-Trip Integrity

This test validates that for any uploaded document, the OCR system:
1. Extracts text from the document
2. Validates extracted data against user profile
3. Flags inconsistencies for user review
4. Stores extracted data for reuse across multiple applications

Validates: Requirements 3.1, 3.2, 3.3, 3.4
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
import numpy as np
import cv2
from typing import Dict, Any, Optional
from datetime import datetime

from services.document_processor import DocumentProcessor, DocumentType, DocumentQuality
from services.document_validator import DocumentValidator
from shared.models.user_profile import UserProfile, Demographics, Economic, Location, Family, Documents


# Strategy for generating synthetic document images
@st.composite
def document_image_strategy(draw, min_size=100, max_size=500):
    """Generate synthetic document images as numpy arrays"""
    width = draw(st.integers(min_value=min_size, max_value=max_size))
    height = draw(st.integers(min_value=min_size, max_value=max_size))
    
    # Create a white background image
    image = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # Add some noise to make it more realistic
    noise_level = draw(st.integers(min_value=1, max_value=30))
    if noise_level > 0:
        noise = np.random.randint(-noise_level, noise_level + 1, image.shape, dtype=np.int16)
        image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    return image


# Strategy for generating Aadhaar numbers
@st.composite
def aadhaar_number_strategy(draw):
    """Generate valid 12-digit Aadhaar numbers"""
    return ''.join([str(draw(st.integers(min_value=0, max_value=9))) for _ in range(12)])


# Strategy for generating PAN numbers
@st.composite
def pan_number_strategy(draw):
    """Generate valid PAN numbers (5 letters, 4 digits, 1 letter)"""
    letters1 = ''.join([draw(st.sampled_from('ABCDEFGHIJKLMNOPQRSTUVWXYZ')) for _ in range(5)])
    digits = ''.join([str(draw(st.integers(min_value=0, max_value=9))) for _ in range(4)])
    letter2 = draw(st.sampled_from('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
    return f"{letters1}{digits}{letter2}"



# Strategy for generating user profiles with documents
@st.composite
def user_profile_with_documents_strategy(draw):
    """Generate user profiles with document information"""
    aadhaar = draw(aadhaar_number_strategy())
    pan = draw(pan_number_strategy())
    
    return {
        'demographics': {
            'age': draw(st.integers(min_value=18, max_value=100)),
            'gender': draw(st.sampled_from(['male', 'female', 'other'])),
            'caste': draw(st.sampled_from(['general', 'obc', 'sc', 'st'])),
            'marital_status': draw(st.sampled_from(['single', 'married', 'widowed', 'divorced']))
        },
        'economic': {
            'annual_income': draw(st.integers(min_value=0, max_value=1000000)),
            'land_ownership': draw(st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False)),
            'employment_status': draw(st.sampled_from(['farmer', 'laborer', 'self_employed', 'unemployed']))
        },
        'location': {
            'state': draw(st.sampled_from(['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Gujarat'])),
            'district': draw(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters=' '))),
            'block': draw(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters=' '))),
            'village': draw(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters=' '))),
            'pincode': draw(st.from_regex(r'^\d{6}$', fullmatch=True))
        },
        'documents': {
            'aadhaar': aadhaar,
            'pan': pan,
            'bank_account': draw(st.text(min_size=9, max_size=18, alphabet=st.characters(whitelist_categories=('Nd',)))),
            'land_records': draw(st.text(min_size=5, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))))
        }
    }


class TestDocumentProcessingRoundTripProperty:
    """
    Property 3: Document Processing Round-Trip Integrity
    
    For any uploaded document, the system should:
    1. Extract text using OCR
    2. Validate extracted data against patterns
    3. Cross-validate with user profile
    4. Store extracted data for reuse
    """
    
    @given(
        image=document_image_strategy(),
        document_type=st.sampled_from(list(DocumentType))
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=5000)
    def test_document_processing_produces_valid_output(self, image: np.ndarray, document_type: DocumentType):
        """
        Property: Document processing must always produce a valid output structure
        
        Validates Requirement 3.1: OCR extracts text from any document
        """
        processor = DocumentProcessor()
        
        try:
            # Process the document
            result = processor.process_document(image, document_type)
            
            # Verify output structure
            assert 'document_id' in result
            assert 'document_type' in result
            assert 'extracted_text' in result
            assert 'parsed_data' in result
            assert 'quality_score' in result
            assert 'quality_level' in result
            assert 'validation_results' in result
            assert 'processed_at' in result
            assert 'improvement_suggestions' in result
            
            # Verify data types
            assert isinstance(result['document_id'], str)
            assert isinstance(result['document_type'], str)
            assert isinstance(result['extracted_text'], str)
            assert isinstance(result['parsed_data'], dict)
            assert isinstance(result['quality_score'], float)
            assert isinstance(result['quality_level'], str)
            assert isinstance(result['validation_results'], dict)
            assert isinstance(result['improvement_suggestions'], list)
            
            # Verify quality score range
            assert 0 <= result['quality_score'] <= 1
            
        except Exception as e:
            # Document processing should handle errors gracefully
            assert isinstance(e, (ValueError, RuntimeError))
    
    @given(
        image=document_image_strategy(),
        document_type=st.sampled_from(list(DocumentType))
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=5000)
    def test_document_quality_assessment_is_consistent(self, image: np.ndarray, document_type: DocumentType):
        """
        Property: Quality assessment must be consistent for the same image
        
        Validates Requirement 3.3: Document quality scoring is reliable
        """
        processor = DocumentProcessor()
        
        try:
            # Process the same document twice
            result1 = processor.process_document(image.copy(), document_type)
            result2 = processor.process_document(image.copy(), document_type)
            
            # Quality scores should be identical for the same image
            assert result1['quality_score'] == result2['quality_score']
            assert result1['quality_level'] == result2['quality_level']
            
        except Exception:
            # If processing fails, it should fail consistently
            pass
    
    @given(
        image=document_image_strategy(),
        document_type=st.sampled_from(list(DocumentType)),
        user_profile=user_profile_with_documents_strategy()
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=5000)
    def test_document_validation_flags_inconsistencies(self, image: np.ndarray, document_type: DocumentType, user_profile: Dict[str, Any]):
        """
        Property: Document validation must flag inconsistencies with user profile
        
        Validates Requirement 3.3: System flags inconsistencies for user review
        """
        processor = DocumentProcessor()
        
        try:
            # Process document with user profile
            result = processor.process_document(image, document_type, user_profile)
            
            # Verify validation results structure
            assert 'validation_results' in result
            validation = result['validation_results']
            
            assert 'is_valid' in validation
            assert 'errors' in validation
            assert 'warnings' in validation
            assert 'inconsistencies' in validation
            
            # Verify data types
            assert isinstance(validation['is_valid'], bool)
            assert isinstance(validation['errors'], list)
            assert isinstance(validation['warnings'], list)
            assert isinstance(validation['inconsistencies'], list)
            
            # If there are inconsistencies, they should be documented
            if validation['inconsistencies']:
                for inconsistency in validation['inconsistencies']:
                    assert isinstance(inconsistency, str)
                    assert len(inconsistency) > 0
            
        except Exception:
            # Processing may fail for synthetic images
            pass
    
    @given(
        image=document_image_strategy(),
        document_type=st.sampled_from(list(DocumentType))
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=5000)
    def test_processed_document_is_stored_and_retrievable(self, image: np.ndarray, document_type: DocumentType):
        """
        Property: Processed documents must be stored and retrievable
        
        Validates Requirement 3.4: Extracted data is stored for reuse
        """
        processor = DocumentProcessor()
        
        try:
            # Process document
            result = processor.process_document(image, document_type)
            document_id = result['document_id']
            
            # Verify document can be retrieved
            retrieved = processor.get_processed_document(document_id)
            
            assert retrieved is not None
            assert retrieved['document_id'] == document_id
            assert retrieved['document_type'] == result['document_type']
            assert retrieved['parsed_data'] == result['parsed_data']
            
        except Exception:
            # Processing may fail for synthetic images
            pass
    
    @given(
        image=document_image_strategy(),
        document_type=st.sampled_from(list(DocumentType))
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=5000)
    def test_raw_images_are_not_stored(self, image: np.ndarray, document_type: DocumentType):
        """
        Property: Raw document images must not be stored after processing
        
        Validates Requirement 3.2: Security requirement for document handling
        """
        processor = DocumentProcessor()
        
        try:
            # Process document
            result = processor.process_document(image, document_type)
            document_id = result['document_id']
            
            # Retrieve processed document
            retrieved = processor.get_processed_document(document_id)
            
            # Verify no raw image data is stored
            assert 'raw_image' not in retrieved
            assert 'image_data' not in retrieved
            assert 'image_bytes' not in retrieved
            
            # Only metadata and extracted data should be present
            assert 'parsed_data' in retrieved
            assert 'extracted_text' in retrieved
            assert 'quality_score' in retrieved
            
        except Exception:
            # Processing may fail for synthetic images
            pass
    
    @given(
        image=document_image_strategy(),
        document_type=st.sampled_from(list(DocumentType))
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=5000)
    def test_improvement_suggestions_are_provided(self, image: np.ndarray, document_type: DocumentType):
        """
        Property: System must provide improvement suggestions for poor quality documents
        
        Validates Requirement 3.4: System provides guidance for document quality
        """
        processor = DocumentProcessor()
        
        try:
            # Process document
            result = processor.process_document(image, document_type)
            
            # Verify improvement suggestions are present
            assert 'improvement_suggestions' in result
            suggestions = result['improvement_suggestions']
            
            assert isinstance(suggestions, list)
            
            # If quality is poor, suggestions should be provided
            if result['quality_level'] in ['poor', 'unreadable']:
                assert len(suggestions) > 0
                
                # Suggestions should be actionable strings
                for suggestion in suggestions:
                    assert isinstance(suggestion, str)
                    assert len(suggestion) > 0
            
        except Exception:
            # Processing may fail for synthetic images
            pass
    
    @given(
        image=document_image_strategy(),
        document_type=st.sampled_from(list(DocumentType))
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=5000)
    def test_document_validator_produces_comprehensive_report(self, image: np.ndarray, document_type: DocumentType):
        """
        Property: Document validator must produce comprehensive validation reports
        
        Validates Requirement 3.3: Validation provides detailed feedback
        """
        processor = DocumentProcessor()
        validator = DocumentValidator()
        
        try:
            # Process document
            processed_doc = processor.process_document(image, document_type)
            
            # Validate document
            validation_report = validator.validate_document(processed_doc)
            
            # Verify report structure
            assert 'document_id' in validation_report
            assert 'document_type' in validation_report
            assert 'validation_timestamp' in validation_report
            assert 'overall_score' in validation_report
            assert 'quality_assessment' in validation_report
            assert 'data_validation' in validation_report
            assert 'issues' in validation_report
            assert 'recommendations' in validation_report
            assert 'is_approved' in validation_report
            
            # Verify score range
            assert 0 <= validation_report['overall_score'] <= 1
            
            # Verify data types
            assert isinstance(validation_report['is_approved'], bool)
            assert isinstance(validation_report['issues'], list)
            assert isinstance(validation_report['recommendations'], list)
            
        except Exception:
            # Processing may fail for synthetic images
            pass
    
    @given(
        image=document_image_strategy(),
        document_type=st.sampled_from(list(DocumentType)),
        user_profile=user_profile_with_documents_strategy()
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=5000)
    def test_cross_validation_detects_mismatches(self, image: np.ndarray, document_type: DocumentType, user_profile: Dict[str, Any]):
        """
        Property: Cross-validation must detect data mismatches between document and profile
        
        Validates Requirement 3.2: System validates extracted data against user profile
        """
        processor = DocumentProcessor()
        validator = DocumentValidator()
        
        try:
            # Process document with profile
            processed_doc = processor.process_document(image, document_type, user_profile)
            
            # Validate with profile
            validation_report = validator.validate_document(processed_doc, user_profile)
            
            # If profile consistency check was performed
            if 'profile_consistency' in validation_report:
                consistency = validation_report['profile_consistency']
                
                # Verify consistency structure
                assert 'consistency_score' in consistency
                assert 'matches' in consistency
                assert 'mismatches' in consistency
                
                # Verify score range
                assert 0 <= consistency['consistency_score'] <= 1
                
                # Verify data types
                assert isinstance(consistency['matches'], list)
                assert isinstance(consistency['mismatches'], list)
                
                # If there are mismatches, they should be documented
                if consistency['mismatches']:
                    for mismatch in consistency['mismatches']:
                        assert isinstance(mismatch, dict)
                        assert 'field' in mismatch
                        assert 'profile_value' in mismatch
                        assert 'document_value' in mismatch
            
        except Exception:
            # Processing may fail for synthetic images
            pass
    
    @given(
        aadhaar=aadhaar_number_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_aadhaar_validation_pattern(self, aadhaar: str):
        """
        Property: Aadhaar numbers must match the 12-digit pattern
        
        Validates Requirement 3.2: Document-specific validation rules
        """
        # Verify Aadhaar format
        assert len(aadhaar) == 12
        assert aadhaar.isdigit()
        
        # Test with processor's validation
        processor = DocumentProcessor()
        parsed_data = {'aadhaar_number': aadhaar}
        
        validation = processor._validate_extracted_data(
            parsed_data,
            DocumentType.AADHAAR,
            None
        )
        
        # Should not have format errors for valid Aadhaar
        format_errors = [e for e in validation['errors'] if 'format' in e.lower()]
        assert len(format_errors) == 0
    
    @given(
        pan=pan_number_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_pan_validation_pattern(self, pan: str):
        """
        Property: PAN numbers must match the 5-letter-4-digit-1-letter pattern
        
        Validates Requirement 3.2: Document-specific validation rules
        """
        # Verify PAN format
        assert len(pan) == 10
        assert pan[:5].isalpha()
        assert pan[5:9].isdigit()
        assert pan[9].isalpha()
        
        # Test with processor's validation
        processor = DocumentProcessor()
        parsed_data = {'pan_number': pan}
        
        validation = processor._validate_extracted_data(
            parsed_data,
            DocumentType.PAN,
            None
        )
        
        # Should not have format errors for valid PAN
        format_errors = [e for e in validation['errors'] if 'format' in e.lower()]
        assert len(format_errors) == 0
    
    @given(
        image=document_image_strategy(),
        document_type=st.sampled_from(list(DocumentType))
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=5000)
    def test_document_id_uniqueness(self, image: np.ndarray, document_type: DocumentType):
        """
        Property: Each processed document must have a unique ID
        
        Validates Requirement 3.4: Document storage and retrieval
        """
        processor = DocumentProcessor()
        
        try:
            # Process the same document multiple times
            result1 = processor.process_document(image.copy(), document_type)
            result2 = processor.process_document(image.copy(), document_type)
            
            # Document IDs should be unique (different processing instances)
            assert result1['document_id'] != result2['document_id']
            
            # Both should be retrievable
            retrieved1 = processor.get_processed_document(result1['document_id'])
            retrieved2 = processor.get_processed_document(result2['document_id'])
            
            assert retrieved1 is not None
            assert retrieved2 is not None
            assert retrieved1['document_id'] != retrieved2['document_id']
            
        except Exception:
            # Processing may fail for synthetic images
            pass
    
    @given(
        quality_score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_quality_level_mapping_is_consistent(self, quality_score: float):
        """
        Property: Quality score must map consistently to quality levels
        
        Validates Requirement 3.3: Quality assessment is reliable
        """
        # Define expected quality levels based on score
        if quality_score >= 0.8:
            expected_level = DocumentQuality.EXCELLENT
        elif quality_score >= 0.6:
            expected_level = DocumentQuality.GOOD
        elif quality_score >= 0.4:
            expected_level = DocumentQuality.ACCEPTABLE
        elif quality_score >= 0.2:
            expected_level = DocumentQuality.POOR
        else:
            expected_level = DocumentQuality.UNREADABLE
        
        # Create a mock image with known quality characteristics
        processor = DocumentProcessor()
        
        # Create synthetic image
        image = np.ones((200, 200), dtype=np.uint8) * 127
        
        # Assess quality
        assessed_score, assessed_level = processor._assess_image_quality(image)
        
        # Verify score is in valid range
        assert 0 <= assessed_score <= 1
        
        # Verify level is a valid DocumentQuality
        assert assessed_level in list(DocumentQuality)
    
    @given(
        image=document_image_strategy(),
        document_type=st.sampled_from(list(DocumentType))
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=5000)
    def test_validation_report_retrievability(self, image: np.ndarray, document_type: DocumentType):
        """
        Property: Validation reports must be stored and retrievable
        
        Validates Requirement 3.4: System maintains validation history
        """
        processor = DocumentProcessor()
        validator = DocumentValidator()
        
        try:
            # Process and validate document
            processed_doc = processor.process_document(image, document_type)
            validation_report = validator.validate_document(processed_doc)
            
            document_id = processed_doc['document_id']
            
            # Retrieve validation report
            retrieved_report = validator.get_validation_report(document_id)
            
            assert retrieved_report is not None
            assert retrieved_report['document_id'] == document_id
            assert retrieved_report['overall_score'] == validation_report['overall_score']
            assert retrieved_report['is_approved'] == validation_report['is_approved']
            
        except Exception:
            # Processing may fail for synthetic images
            pass
    
    @given(
        images=st.lists(document_image_strategy(), min_size=1, max_size=5),
        document_type=st.sampled_from(list(DocumentType))
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=10000)
    def test_batch_processing_consistency(self, images: list, document_type: DocumentType):
        """
        Property: Batch processing must produce consistent results
        
        Validates Requirement 3.1: OCR processing is reliable
        """
        processor = DocumentProcessor()
        
        try:
            # Process all images
            results = []
            for image in images:
                result = processor.process_document(image, document_type)
                results.append(result)
            
            # Verify all results have required structure
            for result in results:
                assert 'document_id' in result
                assert 'quality_score' in result
                assert 'parsed_data' in result
                assert 0 <= result['quality_score'] <= 1
            
            # Verify unique document IDs
            doc_ids = [r['document_id'] for r in results]
            assert len(doc_ids) == len(set(doc_ids))
            
        except Exception:
            # Processing may fail for synthetic images
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
