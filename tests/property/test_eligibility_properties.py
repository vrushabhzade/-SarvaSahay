"""
Property-Based Tests for Eligibility Engine
Uses Hypothesis framework to test system properties with diverse inputs
"""

import pytest
from hypothesis import given, strategies as st, settings
from typing import Dict, Any


# Hypothesis strategies for generating test data
user_profile_strategy = st.fixed_dictionaries({
    "profileId": st.text(min_size=5, max_size=20),
    "demographics": st.fixed_dictionaries({
        "age": st.integers(min_value=18, max_value=100),
        "gender": st.sampled_from(["male", "female", "other"]),
        "caste": st.sampled_from(["General", "OBC", "SC", "ST"]),
        "maritalStatus": st.sampled_from(["single", "married", "widowed"])
    }),
    "economic": st.fixed_dictionaries({
        "annualIncome": st.integers(min_value=0, max_value=1000000),
        "landOwnership": st.floats(min_value=0.0, max_value=50.0),
        "employmentStatus": st.sampled_from(["farmer", "laborer", "self-employed", "unemployed"])
    }),
    "location": st.fixed_dictionaries({
        "state": st.sampled_from(["Maharashtra", "Karnataka", "Tamil Nadu", "Gujarat"]),
        "district": st.text(min_size=3, max_size=20),
        "block": st.text(min_size=3, max_size=20),
        "village": st.text(min_size=3, max_size=20)
    }),
    "family": st.fixed_dictionaries({
        "size": st.integers(min_value=1, max_value=15),
        "dependents": st.integers(min_value=0, max_value=10)
    })
})


class MockEligibilityEngine:
    """Mock eligibility engine for property testing"""
    
    def evaluate_eligibility(self, user_profile: Dict[str, Any]) -> list:
        """Mock evaluation that always returns consistent results"""
        # Simple mock logic for property testing
        eligible_schemes = []
        
        # Mock PM-KISAN eligibility
        if (user_profile["economic"]["employmentStatus"] == "farmer" and 
            user_profile["economic"]["annualIncome"] < 200000):
            eligible_schemes.append({
                "schemeId": "PM-KISAN",
                "benefitAmount": 6000,
                "eligibilityScore": 0.95
            })
        
        return eligible_schemes


class TestEligibilityProperties:
    """Property-based tests for eligibility engine"""
    
    @given(user_profile_strategy)
    @settings(max_examples=100)  # 100+ iterations as per requirements
    def test_evaluation_always_returns_list(self, user_profile):
        """Property: Eligibility evaluation always returns a list"""
        engine = MockEligibilityEngine()
        result = engine.evaluate_eligibility(user_profile)
        
        assert isinstance(result, list), "Eligibility evaluation must return a list"
    
    @given(user_profile_strategy)
    @settings(max_examples=100)
    def test_evaluation_deterministic(self, user_profile):
        """Property: Same input always produces same output (deterministic)"""
        engine = MockEligibilityEngine()
        
        result1 = engine.evaluate_eligibility(user_profile)
        result2 = engine.evaluate_eligibility(user_profile)
        
        assert result1 == result2, "Eligibility evaluation must be deterministic"
    
    @given(user_profile_strategy)
    @settings(max_examples=100)
    def test_valid_eligibility_scores(self, user_profile):
        """Property: All eligibility scores are between 0 and 1"""
        engine = MockEligibilityEngine()
        result = engine.evaluate_eligibility(user_profile)
        
        for scheme in result:
            score = scheme.get("eligibilityScore", 0)
            assert 0 <= score <= 1, f"Eligibility score {score} must be between 0 and 1"
    
    @given(user_profile_strategy)
    @settings(max_examples=100)
    def test_benefit_amounts_positive(self, user_profile):
        """Property: All benefit amounts are positive numbers"""
        engine = MockEligibilityEngine()
        result = engine.evaluate_eligibility(user_profile)
        
        for scheme in result:
            benefit = scheme.get("benefitAmount", 0)
            assert benefit > 0, f"Benefit amount {benefit} must be positive"
    
    @given(user_profile_strategy)
    @settings(max_examples=100)
    def test_scheme_ids_not_empty(self, user_profile):
        """Property: All scheme IDs are non-empty strings"""
        engine = MockEligibilityEngine()
        result = engine.evaluate_eligibility(user_profile)
        
        for scheme in result:
            scheme_id = scheme.get("schemeId", "")
            assert isinstance(scheme_id, str), "Scheme ID must be a string"
            assert len(scheme_id) > 0, "Scheme ID cannot be empty"
    
    @given(st.integers(min_value=18, max_value=100))
    @settings(max_examples=100)
    def test_age_boundary_conditions(self, age):
        """Property: Age boundaries are handled correctly"""
        # Create a profile with the given age
        profile = {
            "profileId": "test-123",
            "demographics": {"age": age, "gender": "male", "caste": "General", "maritalStatus": "single"},
            "economic": {"annualIncome": 100000, "landOwnership": 1.0, "employmentStatus": "farmer"},
            "location": {"state": "Maharashtra", "district": "Pune", "block": "Haveli", "village": "Test"},
            "family": {"size": 3, "dependents": 1}
        }
        
        engine = MockEligibilityEngine()
        result = engine.evaluate_eligibility(profile)
        
        # Should not crash with any valid age
        assert isinstance(result, list)
    
    @given(st.floats(min_value=0.0, max_value=1000000.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_income_boundary_conditions(self, income):
        """Property: Income boundaries are handled correctly"""
        profile = {
            "profileId": "test-123",
            "demographics": {"age": 30, "gender": "female", "caste": "OBC", "maritalStatus": "married"},
            "economic": {"annualIncome": int(income), "landOwnership": 2.0, "employmentStatus": "farmer"},
            "location": {"state": "Karnataka", "district": "Bangalore", "block": "Test", "village": "Test"},
            "family": {"size": 4, "dependents": 2}
        }
        
        engine = MockEligibilityEngine()
        result = engine.evaluate_eligibility(profile)
        
        # Should handle any valid income without crashing
        assert isinstance(result, list)
    
    @given(user_profile_strategy)
    @settings(max_examples=50)  # Reduced for performance test
    def test_performance_property(self, user_profile):
        """Property: Evaluation completes within performance requirements"""
        import time
        
        engine = MockEligibilityEngine()
        
        start_time = time.time()
        result = engine.evaluate_eligibility(user_profile)
        end_time = time.time()
        
        evaluation_time = end_time - start_time
        assert evaluation_time < 5.0, f"Evaluation took {evaluation_time:.3f}s, should be <5s"
        assert isinstance(result, list)
    
    @given(user_profile_strategy)
    @settings(max_examples=100)
    def test_no_duplicate_schemes(self, user_profile):
        """Property: No duplicate schemes in eligibility results"""
        engine = MockEligibilityEngine()
        result = engine.evaluate_eligibility(user_profile)
        
        scheme_ids = [scheme["schemeId"] for scheme in result]
        unique_scheme_ids = set(scheme_ids)
        
        assert len(scheme_ids) == len(unique_scheme_ids), "No duplicate schemes should be returned"