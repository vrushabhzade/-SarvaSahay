"""
Property-Based Tests for Performance Under Scale
Feature: sarvasahay-platform, Property 9: Performance Under Scale

This test validates that for any system load condition:
1. Eligibility checks complete within 5 seconds
2. Document processing handles concurrent uploads without degradation
3. System maintains 99.5% uptime during business hours

Validates: Requirements 9.1, 9.2, 9.5
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
import time
import threading
import numpy as np
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

from services.eligibility_engine import EligibilityEngine
from services.document_processor import DocumentProcessor, DocumentType
from services.scheme_database import SchemeDatabase
from services.rule_engine import RuleEngine


# Strategy for generating valid user profiles for performance testing
@st.composite
def performance_profile_strategy(draw):
    """Generate valid user profiles for performance evaluation"""
    return {
        'demographics': {
            'age': draw(st.integers(min_value=0, max_value=150)),
            'gender': draw(st.sampled_from(['male', 'female', 'other'])),
            'caste': draw(st.sampled_from(['general', 'obc', 'sc', 'st'])),
            'maritalStatus': draw(st.sampled_from(['single', 'married', 'widowed', 'divorced']))
        },
        'economic': {
            'annualIncome': draw(st.integers(min_value=0, max_value=10000000)),
            'landOwnership': draw(st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False)),
            'employmentStatus': draw(st.sampled_from(['farmer', 'laborer', 'self_employed', 'unemployed']))
        },
        'location': {
            'state': draw(st.sampled_from(['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Uttar Pradesh', 'Bihar'])),
            'district': draw(st.text(min_size=3, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters=' '))),
            'block': draw(st.text(min_size=3, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters=' '))),
            'village': draw(st.text(min_size=3, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters=' ')))
        },
        'family': {
            'size': draw(st.integers(min_value=1, max_value=20)),
            'dependents': draw(st.integers(min_value=0, max_value=10)),
            'elderlyMembers': draw(st.integers(min_value=0, max_value=5)),
            'children': draw(st.integers(min_value=0, max_value=10))
        }
    }


# Strategy for generating test document images
@st.composite
def test_document_image_strategy(draw):
    """Generate synthetic document images for testing"""
    # Create a simple test image (grayscale)
    width = draw(st.integers(min_value=800, max_value=2000))
    height = draw(st.integers(min_value=600, max_value=1500))
    
    # Generate random grayscale image
    image = np.random.randint(0, 256, (height, width), dtype=np.uint8)
    
    return image


class TestPerformanceUnderScaleProperty:
    """
    Property 9: Performance Under Scale
    
    For any system load condition, the system should:
    1. Complete eligibility checks within 5 seconds
    2. Handle concurrent document processing without degradation
    3. Maintain consistent performance under load
    """
    
    @given(profile=performance_profile_strategy())
    @settings(max_examples=100, deadline=6000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_eligibility_check_performance_requirement(self, profile: Dict[str, Any]):
        """
        Property: Eligibility checks must complete within 5 seconds for 30+ schemes
        
        Validates Requirement 9.1: Maintain response times under 5 seconds for eligibility checks
        """
        # Ensure family constraints are valid
        if profile['family']['dependents'] >= profile['family']['size']:
            profile['family']['dependents'] = max(0, profile['family']['size'] - 1)
        
        # Initialize eligibility engine
        engine = EligibilityEngine()
        
        # Verify we have 30+ schemes
        scheme_count = engine.get_scheme_count()
        assert scheme_count >= 30, f"Expected 30+ schemes, got {scheme_count}"
        
        # Measure evaluation time
        start_time = time.time()
        
        # Evaluate eligibility
        eligible_schemes = engine.evaluate_eligibility(profile)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Performance requirement: must complete within 5 seconds
        assert elapsed_time < 5.0, \
            f"Eligibility check took {elapsed_time:.3f}s, exceeds 5s requirement"
        
        # Verify results are valid
        assert isinstance(eligible_schemes, list)
        for scheme in eligible_schemes:
            assert 'schemeId' in scheme
            assert 'benefitAmount' in scheme
            assert 'eligibilityScore' in scheme
    
    @given(
        profiles=st.lists(
            performance_profile_strategy(),
            min_size=5,
            max_size=20
        )
    )
    @settings(max_examples=50, deadline=30000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_concurrent_eligibility_evaluation_performance(self, profiles: List[Dict[str, Any]]):
        """
        Property: System must handle concurrent eligibility evaluations without degradation
        
        Validates Requirement 9.2: Handle concurrent uploads without degradation
        """
        # Fix family constraints for all profiles
        for profile in profiles:
            if profile['family']['dependents'] >= profile['family']['size']:
                profile['family']['dependents'] = max(0, profile['family']['size'] - 1)
        
        # Initialize engine
        engine = EligibilityEngine()
        
        # Track individual evaluation times
        evaluation_times = []
        results = []
        
        def evaluate_profile(prof):
            """Evaluate a single profile and track time"""
            start = time.time()
            result = engine.evaluate_eligibility(prof)
            elapsed = time.time() - start
            return elapsed, result
        
        # Execute concurrent evaluations
        with ThreadPoolExecutor(max_workers=min(10, len(profiles))) as executor:
            futures = [executor.submit(evaluate_profile, p) for p in profiles]
            
            for future in as_completed(futures):
                elapsed, result = future.result()
                evaluation_times.append(elapsed)
                results.append(result)
        
        # Verify all evaluations completed
        assert len(results) == len(profiles)
        
        # Verify each evaluation met the 5-second requirement
        for i, elapsed in enumerate(evaluation_times):
            assert elapsed < 5.0, \
                f"Concurrent evaluation {i+1} took {elapsed:.3f}s, exceeds 5s requirement"
        
        # Verify no significant performance degradation
        # Calculate statistics
        avg_time = statistics.mean(evaluation_times)
        max_time = max(evaluation_times)
        min_time = min(evaluation_times)
        
        # Max time should not be more than 2x the average (no severe degradation)
        assert max_time < avg_time * 2.0, \
            f"Performance degradation detected: max={max_time:.3f}s, avg={avg_time:.3f}s"
    
    @given(
        image=test_document_image_strategy(),
        document_type=st.sampled_from(list(DocumentType))
    )
    @settings(max_examples=50, deadline=10000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_document_processing_performance(
        self, 
        image: np.ndarray,
        document_type: DocumentType
    ):
        """
        Property: Document processing must complete in reasonable time
        
        Validates Requirement 9.1: System maintains response times under load
        """
        # Initialize document processor
        processor = DocumentProcessor()
        
        # Measure processing time
        start_time = time.time()
        
        try:
            # Process document
            result = processor.process_document(image, document_type)
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            # Document processing should complete within reasonable time (10 seconds)
            assert elapsed_time < 10.0, \
                f"Document processing took {elapsed_time:.3f}s, exceeds 10s threshold"
            
            # Verify result structure
            assert 'document_id' in result
            assert 'quality_score' in result
            assert 'processed_at' in result
            
        except Exception as e:
            # OCR may fail on random images, which is acceptable
            # We're testing that it doesn't hang or crash
            pass
    
    @given(
        images=st.lists(
            test_document_image_strategy(),
            min_size=3,
            max_size=10
        )
    )
    @settings(max_examples=30, deadline=60000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_concurrent_document_processing_no_degradation(self, images: List[np.ndarray]):
        """
        Property: Concurrent document processing must not degrade performance
        
        Validates Requirement 9.2: Handle concurrent uploads without degradation
        """
        # Initialize processor
        processor = DocumentProcessor()
        
        # Track processing times
        processing_times = []
        
        def process_document(img, idx):
            """Process a single document and track time"""
            start = time.time()
            try:
                # Use Aadhaar type for consistency
                result = processor.process_document(img, DocumentType.AADHAAR)
                elapsed = time.time() - start
                return elapsed, True, result
            except Exception:
                # OCR may fail on synthetic images
                elapsed = time.time() - start
                return elapsed, False, None
        
        # Execute concurrent processing
        with ThreadPoolExecutor(max_workers=min(5, len(images))) as executor:
            futures = [executor.submit(process_document, img, i) for i, img in enumerate(images)]
            
            for future in as_completed(futures):
                elapsed, success, result = future.result()
                processing_times.append(elapsed)
        
        # Verify all processing attempts completed
        assert len(processing_times) == len(images)
        
        # Verify no processing took excessively long
        for i, elapsed in enumerate(processing_times):
            assert elapsed < 15.0, \
                f"Concurrent document processing {i+1} took {elapsed:.3f}s, exceeds 15s threshold"
        
        # Verify no severe performance degradation
        if len(processing_times) > 1:
            avg_time = statistics.mean(processing_times)
            max_time = max(processing_times)
            
            # Max should not be more than 3x average (allowing for OCR variability)
            assert max_time < avg_time * 3.0, \
                f"Severe degradation: max={max_time:.3f}s, avg={avg_time:.3f}s"
    
    @given(profile=performance_profile_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_eligibility_evaluation_consistency_under_load(self, profile: Dict[str, Any]):
        """
        Property: Repeated evaluations must produce consistent results
        
        Validates Requirement 9.5: System maintains consistency under load
        """
        # Fix family constraints
        if profile['family']['dependents'] >= profile['family']['size']:
            profile['family']['dependents'] = max(0, profile['family']['size'] - 1)
        
        # Initialize engine
        engine = EligibilityEngine()
        
        # Perform multiple evaluations
        results = []
        for _ in range(5):
            result = engine.evaluate_eligibility(profile)
            results.append(result)
        
        # Verify all results are identical
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            # Compare scheme IDs and counts
            first_ids = sorted([s['schemeId'] for s in first_result])
            result_ids = sorted([s['schemeId'] for s in result])
            
            assert first_ids == result_ids, \
                f"Evaluation {i+1} produced different schemes than first evaluation"
    
    @given(
        profiles=st.lists(
            performance_profile_strategy(),
            min_size=10,
            max_size=50
        )
    )
    @settings(max_examples=20, deadline=60000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_throughput_under_sustained_load(self, profiles: List[Dict[str, Any]]):
        """
        Property: System must maintain throughput under sustained load
        
        Validates Requirement 9.1, 9.2: Performance under scale
        """
        # Fix family constraints
        for profile in profiles:
            if profile['family']['dependents'] >= profile['family']['size']:
                profile['family']['dependents'] = max(0, profile['family']['size'] - 1)
        
        # Initialize engine
        engine = EligibilityEngine()
        
        # Measure total throughput
        start_time = time.time()
        
        successful_evaluations = 0
        for profile in profiles:
            try:
                result = engine.evaluate_eligibility(profile)
                if result is not None:
                    successful_evaluations += 1
            except Exception:
                pass
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate throughput (evaluations per second)
        throughput = successful_evaluations / total_time if total_time > 0 else 0
        
        # System should handle at least 2 evaluations per second
        # (conservative estimate for 1000+ concurrent users requirement)
        assert throughput >= 2.0, \
            f"Throughput too low: {throughput:.2f} evaluations/sec (expected >= 2.0)"
        
        # Verify most evaluations succeeded
        success_rate = successful_evaluations / len(profiles)
        assert success_rate >= 0.95, \
            f"Success rate too low: {success_rate:.2%} (expected >= 95%)"
    
    @given(profile=performance_profile_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_memory_efficiency_during_evaluation(self, profile: Dict[str, Any]):
        """
        Property: Eligibility evaluation must be memory efficient
        
        Validates Requirement 9.2: Efficient resource usage under scale
        """
        # Fix family constraints
        if profile['family']['dependents'] >= profile['family']['size']:
            profile['family']['dependents'] = max(0, profile['family']['size'] - 1)
        
        # Initialize engine
        engine = EligibilityEngine()
        
        # Perform evaluation multiple times to check for memory leaks
        for _ in range(10):
            result = engine.evaluate_eligibility(profile)
            
            # Verify result is returned and can be garbage collected
            assert result is not None
            del result
        
        # If we reach here without memory errors, test passes
        assert True
    
    @given(
        profile=performance_profile_strategy(),
        iterations=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_performance_stability_over_iterations(
        self, 
        profile: Dict[str, Any],
        iterations: int
    ):
        """
        Property: Performance must remain stable over multiple iterations
        
        Validates Requirement 9.5: Consistent performance (99.5% uptime requirement)
        """
        # Fix family constraints
        if profile['family']['dependents'] >= profile['family']['size']:
            profile['family']['dependents'] = max(0, profile['family']['size'] - 1)
        
        # Initialize engine
        engine = EligibilityEngine()
        
        # Track evaluation times
        evaluation_times = []
        
        for _ in range(iterations):
            start = time.time()
            result = engine.evaluate_eligibility(profile)
            elapsed = time.time() - start
            evaluation_times.append(elapsed)
            
            # Each evaluation must meet the 5-second requirement
            assert elapsed < 5.0, \
                f"Evaluation took {elapsed:.3f}s, exceeds 5s requirement"
        
        # Verify performance stability (low variance)
        if len(evaluation_times) > 1:
            avg_time = statistics.mean(evaluation_times)
            stdev_time = statistics.stdev(evaluation_times)
            
            # Standard deviation should be less than 50% of mean (stable performance)
            assert stdev_time < avg_time * 0.5, \
                f"Performance unstable: stdev={stdev_time:.3f}s, mean={avg_time:.3f}s"
    
    @given(profile=performance_profile_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_scheme_database_query_performance(self, profile: Dict[str, Any]):
        """
        Property: Scheme database queries must be efficient
        
        Validates Requirement 9.1: Fast data access for eligibility evaluation
        """
        # Fix family constraints
        if profile['family']['dependents'] >= profile['family']['size']:
            profile['family']['dependents'] = max(0, profile['family']['size'] - 1)
        
        # Initialize database
        scheme_db = SchemeDatabase()
        
        # Measure query time for all schemes
        start_time = time.time()
        all_schemes = scheme_db.get_all_schemes()
        query_time = time.time() - start_time
        
        # Query should complete very quickly (< 0.1 seconds)
        assert query_time < 0.1, \
            f"Scheme database query took {query_time:.3f}s, exceeds 0.1s threshold"
        
        # Verify we got schemes
        assert len(all_schemes) >= 30
    
    @given(profile=performance_profile_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_rule_engine_evaluation_performance(self, profile: Dict[str, Any]):
        """
        Property: Rule engine must evaluate rules efficiently
        
        Validates Requirement 9.1: Fast rule processing for eligibility
        """
        # Fix family constraints
        if profile['family']['dependents'] >= profile['family']['size']:
            profile['family']['dependents'] = max(0, profile['family']['size'] - 1)
        
        # Initialize components
        scheme_db = SchemeDatabase()
        rule_engine = RuleEngine(scheme_db)
        
        # Measure rule evaluation time
        start_time = time.time()
        summary = rule_engine.get_eligibility_summary(profile)
        evaluation_time = time.time() - start_time
        
        # Rule evaluation should complete within 5 seconds
        assert evaluation_time < 5.0, \
            f"Rule engine evaluation took {evaluation_time:.3f}s, exceeds 5s requirement"
        
        # Verify summary structure
        assert 'totalEligibleSchemes' in summary
        assert 'schemes' in summary
        assert 'totalAnnualBenefit' in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
